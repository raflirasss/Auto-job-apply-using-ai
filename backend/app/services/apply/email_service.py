"""Persisted email applications: preflight, send, record attempt and status."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AgentEvent, AppSetting, ApplicationStatus, ApplyAttempt, Document, Job
from app.services.application_status import set_status
from app.services.apply.email_apply import EmailApplyError, SmtpConfig, build_message, read_subject_body, send
from app.services.apply.preflight import ApplyError, preflight
from app.services.discovery import secret
from app.services.notifications import notify


def smtp_config(db: Session, settings: Settings) -> SmtpConfig | None:
    row = db.get(AppSetting, "smtp")
    password = secret(db, settings, "smtp_password")
    if row is None or not password or not row.value.get("username"):
        return None
    v = row.value
    return SmtpConfig(host=v.get("host", "smtp.gmail.com"), port=int(v.get("port", 465)), username=v["username"],
                      password=password, from_name=v.get("from_name"), use_ssl=bool(v.get("use_ssl", True)))


def _latest_docs(db: Session, app_id: int) -> dict[tuple[str, str], Path]:
    version = db.scalar(select(func.max(Document.version)).where(Document.application_id == app_id))
    docs = db.scalars(select(Document).where(Document.application_id == app_id, Document.version == version)).all()
    return {(d.kind, d.format): Path(d.stored_path) for d in docs if Path(d.stored_path).exists()}


def apply_by_email(db: Session, settings: Settings, job: Job, *, smtp_factory=None) -> ApplyAttempt:
    app, _profile = preflight(db, job, "email")
    cfg = smtp_config(db, settings)
    if cfg is None:
        raise ApplyError("Email sending is not configured. Add your SMTP account in Settings → Email.")
    docs = _latest_docs(db, app.id)
    cv, letter, email_txt = docs.get(("resume", "pdf")), docs.get(("cover_letter", "pdf")), docs.get(("email", "txt"))
    if cv is None or email_txt is None:
        raise ApplyError("Generate documents first (CV and application email are required).")
    already = db.scalar(select(func.count()).select_from(ApplyAttempt).where(
        ApplyAttempt.application_id == app.id, ApplyAttempt.mode == "email", ApplyAttempt.outcome == "submitted"))
    if already:
        raise ApplyError("An application email was already sent for this job.")

    attempt = ApplyAttempt(application_id=app.id, mode="email", outcome="running")
    db.add(attempt)
    db.commit()
    subject, body = read_subject_body(email_txt)
    try:
        msg = build_message(cfg, job.apply_email, subject, body, [p for p in (cv, letter) if p])
        message_id = send(cfg, msg, smtp_factory=smtp_factory)
    except EmailApplyError as exc:
        attempt.outcome, attempt.stop_reason, attempt.detail = "failed", "email_error", str(exc)
        attempt.finished_at = datetime.now(timezone.utc)
        app.error_details = str(exc)
        set_status(db, app, ApplicationStatus.PENDING_ACTION, "email failed", actor="apply")
        app.pending_action = f"Email to {job.apply_email} failed: {exc}"
        notify(db, "warning", f"Email apply failed: {job.title}", str(exc), f"/applications?job={job.id}")
        db.commit()
        return attempt

    now = datetime.now(timezone.utc)
    attempt.outcome, attempt.detail, attempt.finished_at = "submitted", f"Sent to {job.apply_email}", now
    attempt.fields_filled = ["email: CV" + (", cover letter" if letter else "")]
    app.applied_at = now
    app.submission_confirmation = f"[email] accepted by SMTP server, Message-ID {message_id}, to {job.apply_email}"
    app.pending_action = app.error_details = None
    set_status(db, app, ApplicationStatus.APPLIED, "application email sent", actor="apply")
    db.add(AgentEvent(category="apply", message=f"Application email sent for job #{job.id}."))
    notify(db, "success", f"Applied by email: {job.title}", f"Sent to {job.apply_email}.", f"/applications?job={job.id}")
    db.commit()
    return attempt
