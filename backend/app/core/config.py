"""Application settings loaded from environment variables / `.env`.

Secrets (API keys, passwords) are only read from the environment or from the
encrypted credential store - never from committed files.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_secret_key: SecretStr = Field(alias="APP_SECRET_KEY")
    dashboard_password: SecretStr = Field(alias="DASHBOARD_PASSWORD")

    database_url: str = Field(
        default=f"sqlite:///{(ROOT_DIR / 'data' / 'app.db').as_posix()}",
        alias="DATABASE_URL",
    )

    ai_api_key: SecretStr | None = Field(default=None, alias="AI_API_KEY")
    ai_base_url: str | None = Field(default=None, alias="AI_BASE_URL")
    ai_model: str | None = Field(default=None, alias="AI_MODEL")

    data_dir: Path = Field(default=ROOT_DIR / "data", alias="DATA_DIR")
    config_dir: Path = Field(default=ROOT_DIR / "config", alias="CONFIG_DIR")

    session_ttl_hours: int = Field(default=12, alias="SESSION_TTL_HOURS", ge=1, le=24 * 30)
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="CORS_ORIGINS",
    )
    max_upload_mb: int = Field(default=10, alias="MAX_UPLOAD_MB", ge=1, le=50)
    notify_webhook_url: str | None = Field(default=None, alias="NOTIFY_WEBHOOK_URL")
    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")
    browser_headless: bool = Field(default=False, alias="BROWSER_HEADLESS")

    @field_validator("notify_webhook_url", mode="before")
    @classmethod
    def _blank_webhook(cls, v: object) -> object:
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("database_url", mode="before")
    @classmethod
    def _default_db(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return f"sqlite:///{(ROOT_DIR / 'data' / 'app.db').as_posix()}"
        return v

    @field_validator("ai_api_key", "ai_base_url", "ai_model", mode="before")
    @classmethod
    def _blank_is_none(cls, v: object) -> object:
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("app_secret_key")
    @classmethod
    def _secret_strength(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("APP_SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("dashboard_password")
    @classmethod
    def _password_strength(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 8:
            raise ValueError("DASHBOARD_PASSWORD must be at least 8 characters long")
        return v

    @property
    def cv_storage_dir(self) -> Path:
        return self.data_dir / "cv" / "originals"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
