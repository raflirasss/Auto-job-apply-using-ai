"""Agent run bookkeeping: single-run guarantee, idempotency, crash recovery, retry backoff."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AgentEvent, AgentRun

STALE_AFTER = timedelta(minutes=30)  # a running run without heartbeat for this long is considered crashed


class RunAlreadyActive(RuntimeError):
    pass


def now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    # SQLite returns naive datetimes even for timezone=True columns.
    return dt.replace(tzinfo=timezone.utc) if dt is not None and dt.tzinfo is None else dt


def active_run(db: Session) -> AgentRun | None:
    return db.scalars(select(AgentRun).where(AgentRun.status == "running").order_by(AgentRun.id.desc())).first()


def recover_stale(db: Session) -> int:
    """Mark runs left 'running' by a crash/restart as failed. Returns how many were recovered."""
    cutoff = now() - STALE_AFTER
    count = 0
    for run in db.scalars(select(AgentRun).where(AgentRun.status == "running")):
        last = _aware(run.heartbeat_at) or _aware(run.started_at)
        if last is None or last < cutoff:
            run.status = "failed"
            run.finished_at = now()
            run.error = "Interrupted (process stopped or crashed); recovered at startup."
            count += 1
    if count:
        db.add(AgentEvent(category="agent", level="warning", message=f"Recovered {count} interrupted agent run(s)."))
        db.commit()
    return count


def daily_key(day: date, attempt: int) -> str:
    return f"daily:{day.isoformat()}:{attempt}"


def start_run(db: Session, trigger: str, idempotency_key: str | None, attempt: int = 1) -> AgentRun:
    """Create a running AgentRun. Raises RunAlreadyActive if another run is active or the key was used."""
    recover_stale(db)
    if active_run(db) is not None:
        raise RunAlreadyActive("Another agent run is in progress.")
    run = AgentRun(trigger=trigger, status="running", idempotency_key=idempotency_key, attempt=attempt, heartbeat_at=now())
    db.add(run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise RunAlreadyActive(f"Run '{idempotency_key}' was already executed.") from None
    # Double-check: two processes could both pass the first check; the lower id wins.
    others = db.scalars(select(AgentRun).where(AgentRun.status == "running", AgentRun.id != run.id, AgentRun.id < run.id)).first()
    if others is not None:
        run.status, run.finished_at, run.error = "cancelled", now(), "Concurrent run detected."
        db.commit()
        raise RunAlreadyActive("Another agent run is in progress.")
    return run


def heartbeat(db: Session, run: AgentRun) -> None:
    db.execute(update(AgentRun).where(AgentRun.id == run.id).values(heartbeat_at=now()))
    db.commit()


def finish_run(db: Session, run: AgentRun, status: str, summary: dict | None = None, error: str | None = None) -> None:
    run.status = status
    run.finished_at = now()
    run.summary = summary
    run.error = error
    db.commit()


def backoff_seconds(attempt: int, base: int = 60, cap: int = 3600) -> int:
    """Exponential backoff: 60s, 120s, 240s ... capped at 1h."""
    return min(cap, base * 2 ** max(0, attempt - 1))


def run_out(r: AgentRun) -> dict:
    return {
        "id": r.id, "trigger": r.trigger, "status": r.status, "attempt": r.attempt,
        "started_at": _aware(r.started_at).isoformat() if r.started_at else None,
        "finished_at": _aware(r.finished_at).isoformat() if r.finished_at else None,
        "summary": r.summary, "error": r.error,
    }
