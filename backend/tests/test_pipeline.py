"""Daily pipeline: discovery, matching, documents, apply routing (email > form), daily limit."""

from __future__ import annotations

from datetime import datetime, timezone

from app.db.session import get_sessionmaker
from app.models import Application, ApplicationStatus, ApplyAttempt, Job, Notification
from app.services.agent import runs
from app.services.agent.pipeline import run_pipeline
from tests.test_agent_runs import import_job
from tests.test_analysis_api import confirmed_profile


def _pipeline(apply_fn=None, email_fn=None, discovery_fn=None) -> dict:
    from app.core.config import get_settings
    with get_sessionmaker()() as db:
        run = runs.start_run(db, "manual", None)
        out = run_pipeline(db, get_settings(), run, apply_fn=apply_fn, email_fn=email_fn,
                           discovery_fn=discovery_fn or (lambda db, s: {}))
        runs.finish_run(db, run, "succeeded", out)
        return out


def _fake_submit(mode):
    calls = []

    def fn(db, settings, job, *rest):
        calls.append(job.id)
        app = db.query(Application).filter_by(job_id=job.id).one()
        app.applied_at, app.status = datetime.now(timezone.utc), ApplicationStatus.APPLIED
        a = ApplyAttempt(application_id=app.id, mode=mode, outcome="submitted")
        db.add(a)
        db.commit()
        return a
    return fn, calls


def test_without_profile_reports_instead_of_failing(auth_client):
    import_job(auth_client, 1)
    out = _pipeline()
    assert out["analyzed"] == 0
    assert any("No source is enabled" in n for n in out["notes"])
    assert any("profile" in n.lower() for n in out["notes"])


def test_discovery_report_is_summarised(auth_client):
    confirmed_profile(auth_client)
    report = {"rss": {"fetched": 3, "created": 2, "updated": 1, "failed": 0, "errors": ["feed x: timeout"], "notes": []}}
    out = _pipeline(discovery_fn=lambda db, s: report)
    assert out["discovered_new"] == 2 and out["discovery"]["rss"]["fetched"] == 3
    assert "rss: feed x: timeout" in out["notes"]


def test_form_jobs_are_auto_applied(auth_client):
    confirmed_profile(auth_client)
    import_job(auth_client, 1)
    fake, calls = _fake_submit("auto")
    out = _pipeline(apply_fn=fake)
    assert out["documents_generated"] == 1 and out["auto_applied"] == 1 and len(calls) == 1, out
    with get_sessionmaker()() as db:
        assert db.query(Application).one().status == ApplicationStatus.APPLIED
        assert db.query(Notification).filter(Notification.title == "Daily job hunt summary").count() == 1


def test_email_is_preferred_over_form(auth_client):
    confirmed_profile(auth_client)
    import_job(auth_client, 1)
    with get_sessionmaker()() as db:
        db.query(Job).one().apply_email = "hr@example.com"
        db.commit()
    email, email_calls = _fake_submit("email")
    form, form_calls = _fake_submit("auto")
    out = _pipeline(apply_fn=form, email_fn=email)
    assert out["email_applied"] == 1 and email_calls and not form_calls, out


def test_blocked_host_waits_for_owner(auth_client):
    confirmed_profile(auth_client)
    import_job(auth_client, 1)
    with get_sessionmaker()() as db:
        db.query(Job).one().application_url = "https://www.linkedin.com/jobs/view/1"
        db.commit()
    fake, calls = _fake_submit("auto")
    out = _pipeline(apply_fn=fake)
    assert calls == [] and out["awaiting_manual_apply"] == 1


def test_idempotent_documents(auth_client):
    confirmed_profile(auth_client)
    import_job(auth_client, 1)
    _pipeline()
    out = _pipeline()
    assert out["analyzed"] == 0 and out["documents_generated"] == 0


def test_daily_limit(auth_client):
    confirmed_profile(auth_client)
    prefs = auth_client.get("/api/settings/preferences").json()
    auth_client.put("/api/settings/preferences", json={**prefs, "daily_application_limit": 1})
    import_job(auth_client, 1)
    import_job(auth_client, 2)
    fake, calls = _fake_submit("auto")
    out = _pipeline(apply_fn=fake)
    assert len(calls) == 1 and out["auto_applied"] == 1, out
    assert "Daily application limit reached." in out["notes"]


def test_auto_apply_disabled_in_preferences(auth_client):
    confirmed_profile(auth_client)
    prefs = auth_client.get("/api/settings/preferences").json()
    auth_client.put("/api/settings/preferences", json={**prefs, "auto_apply": False})
    import_job(auth_client, 1)
    fake, calls = _fake_submit("auto")
    out = _pipeline(apply_fn=fake)
    assert calls == [] and out["awaiting_manual_apply"] == 1
