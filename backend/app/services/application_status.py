"""Application status transitions with history. Guards prevent claiming unverified submissions."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AgentEvent, Application, ApplicationStatus, ApplicationStatusHistory

S = ApplicationStatus
# Statuses the matching engine may set. It never touches anything at/after "ready_to_apply".
ENGINE_MANAGED = {S.DISCOVERED, S.ANALYZED, S.QUALIFIED, S.REJECTED}
# Statuses reached only through real submission or the owner's manual update.
POST_SUBMISSION = {S.APPLIED, S.INTERVIEW, S.ASSESSMENT, S.ACCEPTED}


class StatusTransitionError(ValueError):
    pass


def set_status(db: Session, app: Application, new: ApplicationStatus, reason: str | None, *, actor: str) -> bool:
    """Record a status change. Returns False when the status is unchanged. Caller commits."""
    if app.status == new:
        return False
    if actor == "engine" and app.status not in ENGINE_MANAGED:
        return False  # engine never overrides a manual/submission status
    if actor == "engine_docs" and app.status not in {S.ANALYZED, S.QUALIFIED}:
        return False
    db.add(ApplicationStatusHistory(application=app, from_status=app.status.value, to_status=new.value, reason=reason))
    app.status = new
    return True


def manual_update(db: Session, app: Application, new: ApplicationStatus, note: str | None, confirmation: str | None) -> Application:
    """Owner-driven update. Marking 'applied' requires the owner's own confirmation text."""
    if new == S.APPLIED:
        if not confirmation or not confirmation.strip():
            raise StatusTransitionError(
                "Marking as applied requires a submission confirmation (e.g. confirmation email date or reference)."
            )
        app.submission_confirmation = f"[manual] {confirmation.strip()}"
        app.applied_at = app.applied_at or datetime.now(timezone.utc)
    if new in POST_SUBMISSION - {S.APPLIED} and app.applied_at is None:
        raise StatusTransitionError("Mark the application as applied (with confirmation) before this status.")
    if new in ENGINE_MANAGED - {S.REJECTED} | {S.READY_TO_APPLY, S.PENDING_ACTION} and app.applied_at is not None:
        raise StatusTransitionError("This application was already submitted; it cannot move back to a pre-application status.")
    if note is not None:
        app.notes = note.strip() or None
    changed = set_status(db, app, new, note or "manual update", actor="owner")
    if changed:
        db.add(AgentEvent(category="applications", message=f"Application #{app.id} status set to '{new.value}' manually."))
    db.commit()
    return app
