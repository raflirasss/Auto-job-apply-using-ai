from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_auth
from app.db.session import get_db
from app.models import AgentEvent, AgentRun, Notification
from app.schemas.settings import SchedulerConfig
from app.services.agent import runs
from app.services.agent.scheduler import agent_scheduler
from app.services.settings_store import get_setting, save_setting

router = APIRouter(prefix="/api/agent", tags=["agent"], dependencies=[Depends(require_auth)])


def _status(db: Session, settings: Settings) -> dict:
    cfg: SchedulerConfig = get_setting(db, settings, "scheduler")  # type: ignore[assignment]
    active = runs.active_run(db)
    last = db.scalars(select(AgentRun).order_by(AgentRun.id.desc()).limit(1)).first()
    return {
        "scheduler_running": agent_scheduler.running,
        "enabled": cfg.enabled,
        "paused": cfg.paused,
        "run_time": cfg.run_time,
        "timezone": cfg.timezone,
        "next_run_time": agent_scheduler.next_run_time(),
        "active_run": runs.run_out(active) if active else None,
        "last_run": runs.run_out(last) if last else None,
    }


@router.get("/status")
def status(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    return _status(db, settings)


def _set(db: Session, settings: Settings, **changes) -> dict:
    cfg: SchedulerConfig = get_setting(db, settings, "scheduler")  # type: ignore[assignment]
    save_setting(db, settings, "scheduler", cfg.model_copy(update=changes))
    db.add(AgentEvent(category="agent", message=f"Scheduler updated: {', '.join(f'{k}={v}' for k, v in changes.items())}."))
    db.commit()
    agent_scheduler.apply_config()
    return _status(db, settings)


@router.post("/start")
def start(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    return _set(db, settings, enabled=True, paused=False)


@router.post("/pause")
def pause(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    return _set(db, settings, paused=True)


@router.post("/resume")
def resume(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    return _set(db, settings, paused=False)


@router.post("/run")
def run_now() -> dict:
    try:
        run_id = agent_scheduler.trigger_manual()
    except runs.RunAlreadyActive as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"run_id": run_id}


@router.get("/runs")
def list_runs(limit: int = Query(default=30, ge=1, le=200), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(AgentRun).order_by(AgentRun.id.desc()).limit(limit)).all()
    return {"runs": [runs.run_out(r) for r in rows]}


@router.get("/events")
def events(limit: int = Query(default=100, ge=1, le=500), run_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    q = select(AgentEvent).order_by(AgentEvent.created_at.desc(), AgentEvent.id.desc()).limit(limit)
    if run_id is not None:
        q = q.where(AgentEvent.run_id == run_id)
    return {"events": [{"id": e.id, "run_id": e.run_id, "level": e.level, "category": e.category, "message": e.message,
                        "created_at": e.created_at.isoformat()} for e in db.scalars(q)]}


@router.get("/notifications")
def notifications(limit: int = Query(default=30, ge=1, le=200), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Notification).order_by(Notification.id.desc()).limit(limit)).all()
    unread = sum(1 for n in db.scalars(select(Notification).where(Notification.read.is_(False))))
    return {"unread": unread, "notifications": [
        {"id": n.id, "level": n.level, "title": n.title, "body": n.body, "link": n.link, "read": n.read,
         "created_at": n.created_at.isoformat()} for n in rows]}


@router.post("/notifications/read")
def mark_read(db: Session = Depends(get_db)) -> dict:
    db.execute(update(Notification).where(Notification.read.is_(False)).values(read=True))
    db.commit()
    return {"ok": True}
