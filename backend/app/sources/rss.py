"""RSS/Atom feeds: Google Alerts ("Deliver to: RSS feed") and any other job feed the owner adds.

Google Alerts results are links to articles/pages that *mention* a vacancy; the listing details live on
the linked site. The adapter therefore keeps the alert snippet as the description and marks the job as
"summary only" so the owner opens the link to check it.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlsplit

import lxml.etree as ET

from app.sources.base import FetchContext, FetchResult, JobSourceAdapter, SourceJob
from app.sources.http import Blocked, PoliteClient
from app.sources.text import clean, html_to_text

ATOM = "{http://www.w3.org/2005/Atom}"
SALARY_HINT = re.compile(r"(?i)(?:gaji|salary|upah)[^.\n]{0,60}?(?:rp\.?|idr)?\s*[\d.,]+\s*(?:jt|juta|rb|ribu)?(?:\s*[-–]\s*(?:rp\.?)?\s*[\d.,]+\s*(?:jt|juta)?)?[^.\n]{0,20}")


def _unwrap_google(url: str) -> str:
    """Google Alerts links are https://www.google.com/url?...&url=<target>; return the target."""
    parts = urlsplit(url)
    if parts.hostname and parts.hostname.endswith("google.com") and parts.path == "/url":
        target = parse_qs(parts.query).get("url", [None])[0]
        if target:
            return target
    return url


def _date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_feed(xml: bytes | str) -> list[dict]:
    """Return [{title, link, summary_html, published, id}] for RSS 2.0 or Atom."""
    data = xml.encode() if isinstance(xml, str) else xml
    root = ET.fromstring(data, parser=ET.XMLParser(resolve_entities=False, no_network=True, recover=True))
    items = []
    for it in root.iter("item"):
        items.append({"title": it.findtext("title"), "link": it.findtext("link"), "summary_html": it.findtext("description"),
                      "published": it.findtext("pubDate"), "id": it.findtext("guid") or it.findtext("link")})
    for e in root.iter(f"{ATOM}entry"):
        link_el = e.find(f"{ATOM}link")
        items.append({"title": e.findtext(f"{ATOM}title"), "link": link_el.get("href") if link_el is not None else None,
                      "summary_html": e.findtext(f"{ATOM}content") or e.findtext(f"{ATOM}summary"),
                      "published": e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated"),
                      "id": e.findtext(f"{ATOM}id")})
    return items


def feed_item_to_job(item: dict, source: str, feed_label: str) -> SourceJob | None:
    title = clean(html_to_text(item.get("title")))
    link = _unwrap_google((item.get("link") or "").strip())
    if not title or not link.startswith("http"):
        return None
    summary = html_to_text(item.get("summary_html"))
    salary = SALARY_HINT.search(summary or "")
    host = urlsplit(link).hostname or ""
    return SourceJob(
        source=source, external_id=f"{source}:{link}", url=link, title=title[:300],
        company=None, description=summary, salary_label=salary.group(0) if salary else None,
        apply_url=link, posted_at=_date(item.get("published")),
        notes=[f"From feed '{feed_label}' ({host}). Summary only: open the link to read the full listing."],
    )


class RssAdapter(JobSourceAdapter):
    name = "rss"
    label = "RSS feeds (Google Alerts, job boards)"

    def __init__(self, client_factory=PoliteClient):
        self._client_factory = client_factory

    def fetch(self, config: dict, ctx: FetchContext) -> FetchResult:
        result = FetchResult()
        feeds = [f for f in config.get("feeds", []) if f.get("url")]
        if not feeds:
            result.notes.append("No RSS feeds configured.")
            return result
        since = datetime.now(timezone.utc) - timedelta(days=ctx.lookback_days)
        # Google Alerts feed URLs are private to the owner and not covered by robots.txt crawling rules.
        with self._client_factory(respect_robots=False) as http:
            for feed in feeds:
                label = feed.get("name") or feed["url"]
                try:
                    items = parse_feed(http.get(feed["url"]).content)
                except Blocked as exc:
                    result.errors.append(f"{label}: {exc}")
                    continue
                except Exception as exc:  # malformed feed / network
                    result.errors.append(f"{label}: {exc.__class__.__name__}: {str(exc)[:150]}")
                    continue
                for item in items:
                    job = feed_item_to_job(item, self.name, label)
                    if job and (job.posted_at is None or job.posted_at >= since):
                        result.jobs.append(job)
            result.requests = http.requests
        result.jobs = result.jobs[: ctx.max_items]
        return result
