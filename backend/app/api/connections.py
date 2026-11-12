"""Owner account connections: SMTP mailbox (email applications) and Telegram (channel reading)."""

from __future__ import annotations

import smtplib
import ssl

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.sources import sources_status, store_secret
from app.core.config import Settings, get_settings
from app.core.security import require_auth
from app.db.session import get_db
from app.models import AgentEvent, AppSetting
from app.schemas.settings import SourcesConfig
from app.services.settings_store import get_setting, save_setting

router = APIRouter(prefix="/api/sources", tags=["connections"], dependencies=[Depends(require_auth)])


class SmtpIn(BaseModel):
    host: str = Field(default="smtp.gmail.com", min_length=3, max_length=200)
    port: int = Field(default=465, ge=1, le=65535)
    use_ssl: bool = True
    username: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    from_name: str | None = Field(default=None, max_length=100)
    password: str | None = Field(default=None, min_length=4, max_length=200)


@router.put("/smtp")
def put_smtp(body: SmtpIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    value = body.model_dump(exclude={"password"})
    row = db.get(AppSetting, "smtp")
    if row is None:
        db.add(AppSetting(key="smtp", value=value))
    else:
        row.value = value
    if body.password:
        store_secret(db, settings, "smtp_password", body.password)
    db.commit()
    return sources_status(db, settings)["smtp"]


@router.post("/smtp/test")
def test_smtp(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    """Log in to the SMTP server without sending anything."""
    from app.services.apply.email_service import smtp_config

    cfg = smtp_config(db, settings)
    if cfg is None:
        raise HTTPException(409, "SMTP is not configured.")
    ctx = ssl.create_default_context()
    try:
        server = (smtplib.SMTP_SSL(cfg.host, cfg.port, context=ctx, timeout=20) if cfg.use_ssl
                  else smtplib.SMTP(cfg.host, cfg.port, timeout=20))
        with server:
            if not cfg.use_ssl:
                server.starttls(context=ctx)
            server.login(cfg.username, cfg.password)
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(422, "Login failed. For Gmail, use an App Password, not your normal password.") from None
    except (smtplib.SMTPException, OSError) as exc:
        raise HTTPException(422, f"Could not connect: {exc.__class__.__name__}") from None
    return {"ok": True}


class TgCodeIn(BaseModel):
    api_id: int = Field(ge=1)
    api_hash: str = Field(min_length=10, max_length=100)
    phone: str = Field(min_length=8, max_length=20, pattern=r"^\+?\d+$")


class TgVerifyIn(BaseModel):
    code: str = Field(min_length=3, max_length=10)
    password: str | None = Field(default=None, max_length=200)


@router.post("/telegram/send-code")
def tg_send_code(body: TgCodeIn) -> dict:
    from app.services.telegram_login import TelegramLoginError, send_code

    try:
        send_code(body.api_id, body.api_hash, body.phone)
    except TelegramLoginError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"sent": True}


@router.post("/telegram/verify")
def tg_verify(body: TgVerifyIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    from app.services.telegram_login import TelegramLoginError, verify

    try:
        api_id, api_hash, session = verify(body.code, body.password)
    except TelegramLoginError as exc:
        raise HTTPException(422, str(exc)) from exc
    store_secret(db, settings, "telegram_api_hash", api_hash)
    store_secret(db, settings, "telegram_session", session)
    cfg: SourcesConfig = get_setting(db, settings, "sources")  # type: ignore[assignment]
    cfg.telegram.api_id, cfg.telegram.method = api_id, "api"
    save_setting(db, settings, "sources", cfg)
    db.add(AgentEvent(category="settings", message="Telegram account connected."))
    db.commit()
    return {"connected": True}


@router.post("/telegram/disconnect")
def tg_disconnect(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    store_secret(db, settings, "telegram_session", None)
    store_secret(db, settings, "telegram_api_hash", None)
    cfg: SourcesConfig = get_setting(db, settings, "sources")  # type: ignore[assignment]
    cfg.telegram.method = "preview"
    save_setting(db, settings, "sources", cfg)
    db.commit()
    return {"connected": False}
