from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.crypto import encrypt_secret, mask_secret
from app.services.ai_config import resolve_ai_config
from app.core.security import require_auth
from app.db.session import get_db
from app.models import AgentEvent, AppSetting, StoredCredential
from app.schemas.settings import AIConfigIn, AIConfigOut, Preferences, SchedulerConfig
from app.services.settings_store import get_setting, save_setting

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_auth)])


@router.get("/preferences", response_model=Preferences)
def get_preferences(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return get_setting(db, settings, "preferences")


@router.put("/preferences", response_model=Preferences)
def put_preferences(body: Preferences, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    saved = save_setting(db, settings, "preferences", body)
    db.add(AgentEvent(category="settings", message="Job preferences updated."))
    db.commit()
    return saved


@router.get("/scheduler", response_model=SchedulerConfig)
def get_scheduler(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return get_setting(db, settings, "scheduler")


@router.put("/scheduler", response_model=SchedulerConfig)
def put_scheduler(body: SchedulerConfig, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return save_setting(db, settings, "scheduler", body)


def _ai_config(db: Session, settings: Settings) -> AIConfigOut:
    cfg = resolve_ai_config(db, settings)
    return AIConfigOut(
        base_url=cfg.base_url,
        model=cfg.model,
        api_key_masked=mask_secret(cfg.api_key),
        api_key_source=cfg.key_source,
        configured=cfg.configured,
    )


@router.get("/ai", response_model=AIConfigOut)
def get_ai(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _ai_config(db, settings)


@router.put("/ai", response_model=AIConfigOut)
def put_ai(body: AIConfigIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    row = db.get(AppSetting, "ai")
    value = {"base_url": body.base_url, "model": body.model}
    if row is None:
        db.add(AppSetting(key="ai", value=value))
    else:
        row.value = value
    cred = db.get(StoredCredential, "ai_api_key")
    if body.clear_api_key and cred is not None:
        db.delete(cred)
    elif body.api_key:
        ciphertext = encrypt_secret(body.api_key, settings)
        if cred is None:
            db.add(StoredCredential(name="ai_api_key", ciphertext=ciphertext))
        else:
            cred.ciphertext = ciphertext
    db.add(AgentEvent(category="settings", message="AI configuration updated."))
    db.commit()
    return _ai_config(db, settings)
