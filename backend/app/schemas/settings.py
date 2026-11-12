"""Editable configuration schemas (preferences.json, sources.json, scheduler)."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WorkArrangement = Literal["onsite", "hybrid", "remote"]
EmploymentType = Literal["full_time", "part_time", "contract", "internship", "freelance", "temporary"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Preferences(_Model):
    job_sources: list[str] = Field(default_factory=lambda: ["rss", "telegram", "ats"], max_length=10)  # legacy, informational
    location: list[str] = Field(min_length=1, max_length=50)
    work_arrangement: list[WorkArrangement] = Field(min_length=1)
    employment_types: list[EmploymentType] = Field(min_length=1)
    minimum_salary: int = Field(ge=0, le=1_000_000_000)
    salary_currency: Literal["IDR"] = "IDR"
    salary_period: Literal["monthly"] = "monthly"
    allow_undisclosed_salary_review: bool = True
    search_frequency: Literal["daily"] = "daily"
    lookback_days: int = Field(ge=1, le=31)
    minimum_match_score: int = Field(ge=0, le=100)
    review_threshold: int = Field(ge=0, le=100)
    auto_apply: bool
    daily_application_limit: int = Field(ge=0, le=100)
    avoid_duplicates: bool = True
    allow_remote: bool = Field(
        default=False, description="Fully remote jobs are rejected unless explicitly enabled."
    )

    @field_validator("job_sources", "location")
    @classmethod
    def _clean_list(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for item in v:
            item = item.strip()
            if not item or len(item) > 100:
                raise ValueError("entries must be 1-100 characters")
            if item.lower() not in {x.lower() for x in out}:
                out.append(item)
        return out

    @model_validator(mode="after")
    def _consistency(self) -> Preferences:
        if self.review_threshold > self.minimum_match_score:
            raise ValueError("review_threshold must be <= minimum_match_score")
        if "remote" in self.work_arrangement and not self.allow_remote:
            raise ValueError("enable allow_remote before adding 'remote' to work_arrangement")
        return self


_SLUG = r"^[A-Za-z0-9_.-]{2,80}$"


class RssFeed(_Model):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=10, max_length=1000, pattern=r"^https?://")


class RssSource(_Model):
    enabled: bool = False
    feeds: list[RssFeed] = Field(default_factory=list, max_length=50)


class TelegramSource(_Model):
    enabled: bool = False
    method: Literal["api", "preview"] = "api"
    channels: list[str] = Field(default_factory=list, max_length=50)
    messages_per_channel: int = Field(default=100, ge=10, le=500)
    api_id: int | None = Field(default=None, ge=1)
    # api_hash and the login session are secrets: stored encrypted in stored_credentials, never here.

    @field_validator("channels")
    @classmethod
    def _channels(cls, v: list[str]) -> list[str]:
        out = []
        for raw in v:
            name = raw.strip().removeprefix("https://t.me/").removeprefix("s/").removeprefix("@").strip("/")
            if not re.fullmatch(r"[A-Za-z0-9_]{4,64}", name):
                raise ValueError(f"invalid Telegram channel: {raw!r} (use the public @username)")
            if name.lower() not in {c.lower() for c in out}:
                out.append(name)
        return out


class AtsSource(_Model):
    enabled: bool = False
    lever: list[str] = Field(default_factory=list, max_length=100)
    greenhouse: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("lever", "greenhouse")
    @classmethod
    def _slugs(cls, v: list[str]) -> list[str]:
        out = []
        for s in v:
            s = s.strip().lower()
            if not re.fullmatch(_SLUG, s):
                raise ValueError(f"invalid board token: {s!r}")
            if s not in out:
                out.append(s)
        return out


class SourcesConfig(_Model):
    rss: RssSource = Field(default_factory=RssSource)
    telegram: TelegramSource = Field(default_factory=TelegramSource)
    ats: AtsSource = Field(default_factory=AtsSource)
    fetch_interval_hours: int = Field(default=6, ge=1, le=24)


class SchedulerConfig(_Model):
    enabled: bool = False
    run_time: str = Field(default="08:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: Literal["Asia/Jakarta"] = "Asia/Jakarta"
    max_retries: int = Field(default=3, ge=0, le=10)
    paused: bool = False


class AIConfigIn(_Model):
    base_url: str | None = Field(default=None, max_length=300, pattern=r"^https?://")
    model: str | None = Field(default=None, max_length=200)
    api_key: str | None = Field(default=None, min_length=8, max_length=500)
    clear_api_key: bool = False


class AIConfigOut(BaseModel):
    base_url: str | None
    model: str | None
    api_key_masked: str | None
    api_key_source: Literal["environment", "dashboard", "none"]
    configured: bool
