"""Persist apply attempts and drive the browser runner.

Browser session data (cookies from the owner's own login) lives in data/browser_profile/,
which is git-ignored and never read or exported by the app.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AgentEvent, Application, ApplicationStatus, ApplyAttempt, Job
from app.services.application_status import set_status
from app.services.apply.preflight import ApplyError, latest_files, preflight
from app.services.apply.runner import RunResult, run_application
from app.services.notifications import notify

log = logging.getLogger(__name__)
browser_lock = threading.Lock()  # one browser automation at a time, across scheduler and API

__all__ = ["ApplyError", "apply_job", "record_result"]


def _pending_text(result: RunResult) -> str:
    return result.detail + ("\n" + "\n".join(result.fields_unresolved) if result.fields_unresolved else "")


def record_result(db: Session, attempt: ApplyAttempt, app: Application, job: Job, result: RunResult) -> None:
    attempt.outcome = result.outcome
    attempt.stop_reason = result.stop_reason
    attempt.detail = result.detail
    attempt.fields_filled = result.fields_filled
    attempt.fields_unresolved = result.fields_unresolved
    attempt.screenshot_path = result.screenshot
    attempt.finished_at = datetime.now(timezone.utc)
    link = f"/applications?job={job.id}"

    if result.outcome == "submitted" and result.confirmation:
        app.submission_confirmation = f"[auto] {result.confirmation}"
        app.applied_at = datetime.now(timezone.utc)
        app.pending_action = app.error_details = None
        set_status(db, app, ApplicationStatus.APPLIED, "submission confirmed by page", actor="apply")
        notify(db, "success", f"Applied: {job.title}", f"Submission confirmed for {job.company or job.title}.", link)
    elif result.outcome == "awaiting_user":
        app.pending_action = _pending_text(result)
        set_status(db, app, ApplicationStatus.PENDING_ACTION, "assisted apply: awaiting your submission", actor="apply")
    elif result.stop_reason == "job_closed":
        job.is_available = False
        app.error_details = result.detail
        set_status(db, app, ApplicationStatus.FAILED, result.detail, actor="apply")
    else:
        app.pending_action = _pending_text(result)
        app.error_details = f"{result.stop_reason}: {result.detail}"
        set_status(db, app, ApplicationStatus.PENDING_ACTION, result.stop_reason, actor="apply")
        notify(db, "warning", f"Action needed: {job.title}", result.detail, link)
    level = "info" if result.outcome in {"submitted", "awaiting_user"} else "warning"
    suffix = f" ({result.stop_reason})" if result.stop_reason else ""
    db.add(AgentEvent(category="apply", level=level, message=f"Apply attempt #{attempt.id} for job #{job.id}: {result.outcome}{suffix}"))
    db.commit()


def apply_job(db: Session, settings: Settings, job: Job, mode: str, *,
              page_factory: Callable | None = None, keep_open_seconds: int = 0) -> ApplyAttempt:
    """Run one attempt. `page_factory` (tests) yields a context manager producing a page."""
    app, profile = preflight(db, job, mode)
    if not browser_lock.acquire(blocking=False):
        raise ApplyError("Another browser automation is running. Try again when it finishes.")
    try:
        attempt = ApplyAttempt(application_id=app.id, mode=mode, outcome="running")
        db.add(attempt)
        db.commit()
        shot = settings.data_dir / "screenshots" / f"attempt_{attempt.id}.png"
        factory = page_factory or (lambda: open_browser_page(settings))
        recorded = False
        try:
            with factory() as page:
                result = run_application(page, job.application_url, profile, latest_files(db, app.id), mode=mode, screenshot_path=shot)
                # Record first so the dashboard shows the outcome while the owner works in the browser.
                record_result(db, attempt, app, job, result)
                recorded = True
                if result.outcome == "awaiting_user" and keep_open_seconds:
                    _wait_for_user(page, keep_open_seconds)
        except Exception as exc:  # browser crashed / not installed
            log.warning("Browser automation error: %s", exc.__class__.__name__)
            if not recorded:
                db.rollback()
                record_result(db, attempt, app, job, RunResult(
                    "failed", "browser_error", f"Browser automation error: {exc.__class__.__name__}: {str(exc)[:200]}"))
        return attempt
    finally:
        browser_lock.release()


def _wait_for_user(page, seconds: int) -> None:
    """Keep the visible browser open so the owner can finish; ends early when they close it."""
    try:
        page.wait_for_event("close", timeout=seconds * 1000)
    except Exception:
        pass


def open_browser_page(settings: Settings):
    """Persistent Chromium profile so a login the owner did once on an employer site is reused. Visible by default."""
    from contextlib import contextmanager

    from playwright.sync_api import sync_playwright

    @contextmanager
    def _ctx():
        profile_dir = settings.data_dir / "browser_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(str(profile_dir), headless=settings.browser_headless,
                                                           locale="id-ID", timezone_id="Asia/Jakarta")
            try:
                page = context.pages[0] if context.pages else context.new_page()
                yield page
            finally:
                context.close()

    return _ctx()
