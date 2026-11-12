"""Resolve effective AI provider settings (dashboard overrides > environment)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.crypto import decrypt_secret
from app.models import AppSetting, StoredCredential


@dataclass(frozen=True)
class ResolvedAIConfig:
    base_url: str | None
    model: str | None
    api_key: str | None
    key_source: str  # dashboard | environment | none

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)


def resolve_ai_config(db: Session, settings: Settings) -> ResolvedAIConfig:
    row = db.get(AppSetting, "ai")
    overrides = row.value if row else {}
    cred = db.get(StoredCredential, "ai_api_key")
    if cred is not None:
        key, source = decrypt_secret(cred.ciphertext, settings), "dashboard"
    elif settings.ai_api_key is not None:
        key, source = settings.ai_api_key.get_secret_value(), "environment"
    else:
        key, source = None, "none"
    return ResolvedAIConfig(
        base_url=overrides.get("base_url") or settings.ai_base_url,
        model=overrides.get("model") or settings.ai_model,
        api_key=key,
        key_source=source if key else "none",
    )
