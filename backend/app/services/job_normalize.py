"""URL, salary and location normalisation shared by all ingestion paths."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "tracking", "ref",
                   "referrer", "gh_src", "lever-source", "fbclid", "gclid"}
BLOCKED_HOSTS = ("jobstreet.com",)  # removed source: robots.txt + Cloudflare disallow automated access


def canonicalize_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Job URL must be an http(s) URL")
    host = parts.hostname.lower().rstrip(".")
    if any(host == h or host.endswith("." + h) for h in BLOCKED_HOSTS):
        raise ValueError("JobStreet is not supported as a source.")
    port = f":{parts.port}" if parts.port else ""
    path = re.sub(r"/{2,}", "/", parts.path or "/").rstrip("/") or "/"
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False) if k.lower() not in TRACKING_PARAMS]
    return urlunsplit(("https", host + port, path, urlencode(sorted(query)), ""))


def normalize_salary(value: float | None, period: str | None) -> float | None:
    if value is None:
        return None
    if value < 0:
        raise ValueError("Salary cannot be negative")
    factors = {"monthly": 1, "month": 1, "annual": 1 / 12, "yearly": 1 / 12, "weekly": 52 / 12, "week": 52 / 12,
               "daily": 26, "day": 26}
    p = (period or "monthly").lower()
    if p not in factors:
        raise ValueError("Salary period must be monthly, annual, weekly, or daily")
    return round(value * factors[p], 2)


def normalize_location(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()[:300] or None
