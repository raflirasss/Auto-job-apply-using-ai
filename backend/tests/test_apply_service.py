"""Apply service: preflight, persistence, status updates, with a mocked (local-HTML) browser."""

from __future__ import annotations

from contextlib import contextmanager

import pytest

from app.db.session import get_sessionmaker
from app.models import Application, ApplicationStatus, ApplyAttempt, Job
from app.services.apply.runner import RunResult
from tests.apply_pages import GOOD_FORM, LOGIN
from tests.test_agent_runs import import_job
from tests.test_analysis_api import confirmed_profile

pytest.importorskip("playwright.sync_api")


def _page_factory(html):
    from playwright.sync_api import sync_playwright

    @contextmanager
    def factory():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.route("**/*", lambda r: r.fulfill(status=200, content_type="text/html", body=html))
            try:
                yield page
            finally:
                b.close()
    return factory


def _ready_job(client) -> int:
    confirmed_profile(client)
    job_id = import_job(client, 7)
    assert client.post(f"/api/jobs/{job_id}/analyze").status_code == 200
    assert client.post(f"/api/jobs/{job_id}/documents").status_code == 200
    return job_id


def _apply(job_id, mode, factory):
    from app.core.config import get_settings
    from app.services.apply.service import apply_job

    with get_sessionmaker()() as db:
        attempt = apply_job(db, get_settings(), db.get(Job, job_id), mode, page_factory=factory)
        app = db.query(Application).one()
        return attempt, app


def test_apply_preflight_rules(auth_client):
    job_id = import_job(auth_client, 5)
    st = auth_client.get(f"/api/jobs/{job_id}/apply/status").json()
    assert st["allowed_modes"] == ["assisted", "auto"]
    assert st["blocked_reason"]["assisted"] and st["blocked_reason"]["auto"]  # no confirmed profile yet
    assert auth_client.post(f"/api/jobs/{job_id}/apply", json={"mode": "auto"}).status_code == 409
    assert auth_client.post(f"/api/jobs/{job_id}/apply", json={"mode": "email"}).status_code == 409


def test_stop_is_recorded_with_screenshot(auth_client):
    job_id = _ready_job(auth_client)
    attempt, app = _apply(job_id, "assisted", _page_factory(LOGIN))
    assert attempt.outcome == "stopped" and attempt.stop_reason == "login_required"
    assert app.status == ApplicationStatus.PENDING_ACTION and "Login required" in app.pending_action
    shot = auth_client.get(f"/api/apply-attempts/{attempt.id}/screenshot")
    assert shot.status_code == 200 and shot.content[:4] == b"\x89PNG"


def test_assisted_apply_never_marks_applied(auth_client):
    job_id = _ready_job(auth_client)
    attempt, app = _apply(job_id, "assisted", _page_factory(GOOD_FORM))
    assert attempt.outcome == "awaiting_user" and "Full name" in attempt.fields_filled
    assert app.status == ApplicationStatus.PENDING_ACTION and app.applied_at is None


def test_assisted_result_recorded_before_waiting_for_user(auth_client):
    """While the browser stays open for the owner, the dashboard must already show the outcome."""
    from app.core.config import get_settings
    from app.services.apply import service

    job_id = _ready_job(auth_client)
    seen = {}

    def fake_wait(page, seconds):
        with get_sessionmaker()() as other:
            seen["outcome"] = other.query(ApplyAttempt).one().outcome

    original = service._wait_for_user
    service._wait_for_user = fake_wait
    try:
        with get_sessionmaker()() as db:
            service.apply_job(db, get_settings(), db.get(Job, job_id), "assisted",
                              page_factory=_page_factory(GOOD_FORM), keep_open_seconds=5)
    finally:
        service._wait_for_user = original
    assert seen["outcome"] == "awaiting_user"


def test_browser_crash_is_recorded_as_failed(auth_client):
    job_id = _ready_job(auth_client)

    @contextmanager
    def broken():
        raise RuntimeError("Executable doesn't exist")
        yield  # pragma: no cover

    attempt, _ = _apply(job_id, "assisted", broken)
    assert attempt.outcome == "failed" and attempt.stop_reason == "browser_error"


def test_submitted_result_sets_applied_and_blocks_duplicates(auth_client):
    from app.services.apply.service import record_result

    job_id = _ready_job(auth_client)
    with get_sessionmaker()() as db:
        app = db.query(Application).one()
        a = ApplyAttempt(application_id=app.id, mode="auto", outcome="running")
        db.add(a)
        db.commit()
        record_result(db, a, app, db.get(Job, job_id), RunResult("submitted", confirmation="Thank you for applying"))
        assert app.status == ApplicationStatus.APPLIED
        assert app.submission_confirmation == "[auto] Thank you for applying"
    assert auth_client.post(f"/api/jobs/{job_id}/apply", json={"mode": "assisted"}).status_code == 409
