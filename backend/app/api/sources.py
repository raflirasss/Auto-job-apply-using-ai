"""Job sources (RSS, Telegram, company boards) and discovery runs."""

from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.crypto import encrypt_secret
from app.core.security import require_auth
from app.db.session import get_db, get_sessionmaker
from app.models import AgentEvent, AppSetting, StoredCredential
from app.schemas.settings import SourcesConfig
from app.services.discovery import discovery_lock, run_discovery
from app.services.settings_store import get_setting, save_setting

router = APIRouter(prefix="/api/sources", tags=["sources"], dependencies=[Depends(require_auth)])
_last_report: dict = {}


def store_secret(db: Session, settings: Settings, name: str, value: str | None) -> None:
    row = db.get(StoredCredential, name)
    if value is None:
        if row is not None:
            db.delete(row)
        return
    if row is None:
        db.add(StoredCredential(name=name, ciphertext=encrypt_secret(value, settings)))
    else:
        row.ciphertext = encrypt_secret(value, settings)


def sources_status(db: Session, settings: Settings) -> dict:
    cfg = get_setting(db, settings, "sources")
    smtp = db.get(AppSetting, "smtp")
    return {
        "config": cfg.model_dump(),
        "telegram_connected": bool(db.get(StoredCredential, "telegram_session")),
        "smtp": {**(smtp.value if smtp else {}), "password_set": bool(db.get(StoredCredential, "smtp_password"))},
        "discovery_running": discovery_lock.locked(),
        "last_report": _last_report,
    }


@router.get("")
def get_sources(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    return sources_status(db, settings)


@router.put("")
def put_sources(body: SourcesConfig, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    save_setting(db, settings, "sources", body)
    db.add(AgentEvent(category="settings", message="Job sources updated."))
    db.commit()
    from app.services.agent.scheduler import agent_scheduler

    agent_scheduler.apply_config()  # the discovery interval may have changed
    return sources_status(db, settings)


@router.post("/run")
def run_now(settings: Settings = Depends(get_settings)) -> dict:
    if discovery_lock.locked():
        raise HTTPException(409, "Discovery is already running.")

    def worker() -> None:
        global _last_report
        with get_sessionmaker()() as db:
            _last_report = run_discovery(db, settings)

    threading.Thread(target=worker, daemon=True, name="discovery-now").start()
    return {"started": True}
