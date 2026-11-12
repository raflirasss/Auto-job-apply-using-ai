from __future__ import annotations

from collections.abc import Callable

from app.sources.base import JobSourceAdapter, SourceUnavailableError

_REGISTRY: dict[str, Callable[[], JobSourceAdapter]] = {}


def register_source(name: str, factory: Callable[[], JobSourceAdapter]) -> None:
    _REGISTRY[name] = factory


def available_sources() -> list[str]:
    _ensure_defaults()
    return sorted(_REGISTRY)


def get_adapter(name: str) -> JobSourceAdapter:
    _ensure_defaults()
    try:
        return _REGISTRY[name]()
    except KeyError:
        raise SourceUnavailableError(f"Unknown source '{name}'.") from None


def _ensure_defaults() -> None:
    if _REGISTRY:
        return
    from app.sources.ats import AtsAdapter
    from app.sources.rss import RssAdapter
    from app.sources.telegram import TelegramAdapter

    register_source("rss", RssAdapter)
    register_source("telegram", TelegramAdapter)
    register_source("ats", AtsAdapter)
