"""Source integration contract.

Every job source is an isolated adapter implementing `JobSourceAdapter`. Only sources with a
documented public API/feed (or the owner's own account) are implemented; nothing scrapes pages
that disallow it. Adding a source never touches core code: register an adapter in registry.py.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime


class SourceUnavailableError(RuntimeError):
    """Raised when a source cannot be used (not configured, blocked, auth required...)."""


@dataclass
class SourceJob:
    """A listing normalised by an adapter, ready for ingestion (salary still as a raw label)."""

    source: str
    external_id: str
    url: str
    title: str
    company: str | None = None
    location: str | None = None
    work_arrangement: str | None = None
    employment_type: str | None = None
    salary_label: str | None = None
    salary_min: float | None = None  # structured salary (APIs); takes precedence over the label
    salary_max: float | None = None
    salary_period: str = "monthly"
    description: str | None = None
    apply_url: str | None = None
    apply_email: str | None = None
    posted_at: datetime | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class FetchResult:
    jobs: list[SourceJob] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    requests: int = 0


@dataclass
class FetchContext:
    """Owner preferences an adapter may use to limit what it returns."""

    lookback_days: int = 7
    accepted_locations: list[str] = field(default_factory=list)
    max_items: int = 200


class JobSourceAdapter(abc.ABC):
    name: str
    label: str

    @abc.abstractmethod
    def fetch(self, config: dict, ctx: FetchContext) -> FetchResult:
        """Return recent listings. Must never raise for per-item problems: report them in errors."""
