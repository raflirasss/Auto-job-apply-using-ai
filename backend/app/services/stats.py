"""Dashboard statistics computed only from real database rows."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AgentEvent, Application, ApplicationStatus, Job

S = ApplicationStatus
PENDING = {S.READY_TO_APPLY, S.PENDING_ACTION}
QUALIFIED_STAGE = {S.QUALIFIED, S.READY_TO_APPLY, S.PENDING_ACTION}
POSITIVE = {S.INTERVIEW, S.ASSESSMENT, S.ACCEPTED}


def overview(db: Session) -> dict:
    """`rejected` is shared by hard-filter rejects (never applied) and employer rejections
    (applied_at set); submission-based numbers therefore always require applied_at."""
    counts = {s: c for s, c in db.execute(select(Application.status, func.count()).group_by(Application.status))}
    applied = {s: c for s, c in db.execute(
        select(Application.status, func.count()).where(Application.applied_at.is_not(None)).group_by(Application.status))}

    submitted = sum(applied.values())
    positive = sum(applied.get(s, 0) for s in POSITIVE)
    employer_rejections = applied.get(S.REJECTED, 0)
    events = db.scalars(select(AgentEvent).order_by(AgentEvent.created_at.desc(), AgentEvent.id.desc()).limit(15)).all()
    return {
        "jobs_discovered": db.scalar(select(func.count()).select_from(Job)) or 0,
        "qualified": sum(counts.get(s, 0) for s in QUALIFIED_STAGE) + submitted,
        "applications_submitted": submitted,
        "pending": sum(counts.get(s, 0) for s in PENDING),
        "interviews": counts.get(S.INTERVIEW, 0),
        "rejections": employer_rejections,
        "filtered_out": counts.get(S.REJECTED, 0) - employer_rejections,
        "success_rate": round(positive / submitted * 100, 1) if submitted else None,
        "status_counts": {s.value: counts.get(s, 0) for s in ApplicationStatus},
        "recent_activity": [
            {
                "id": e.id,
                "level": e.level,
                "category": e.category,
                "message": e.message,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }
