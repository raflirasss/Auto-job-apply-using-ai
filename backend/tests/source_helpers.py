"""Mock HTTP layer for source adapter tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx

from app.sources.base import FetchContext
from app.sources.http import PoliteClient

RECENT = (datetime.now(timezone.utc) - timedelta(hours=3)).replace(microsecond=0)
ISO = RECENT.isoformat().replace("+00:00", "Z")
RFC = format_datetime(RECENT)
CTX = FetchContext(lookback_days=7, accepted_locations=["Jakarta", "Jakarta Utara", "Bekasi"])


def client_for(routes: dict[str, tuple[int, str]]):
    """PoliteClient factory answering from `routes` (URL prefix -> (status, body)); anything else 404."""

    def handler(request: httpx.Request) -> httpx.Response:
        for prefix, (status, body) in routes.items():
            if str(request.url).startswith(prefix):
                return httpx.Response(status, text=body)
        return httpx.Response(404, text="")

    def factory(**kw):
        return PoliteClient(httpx.Client(transport=httpx.MockTransport(handler)), min_interval=0, **kw)
    return factory
