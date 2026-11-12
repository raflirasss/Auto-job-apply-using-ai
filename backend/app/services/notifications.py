"""Notifications: always stored for the dashboard; optionally POSTed to a webhook.

Webhook URL comes from the NOTIFY_WEBHOOK_URL setting (e.g. a Discord/Slack/ntfy endpoint).
Payloads contain titles and short summaries only, never documents or contact details.
"""

from __future__ import annotations

import logging

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Notification

log = logging.getLogger(__name__)


def notify(db: Session, level: str, title: str, body: str, link: str | None = None) -> Notification:
    """Add a notification to the session (caller commits). Webhook delivery is best-effort."""
    n = Notification(level=level, title=title[:200], body=body[:2000], link=link)
    db.add(n)
    url = get_settings().notify_webhook_url
    if url:
        try:
            r = httpx.post(url, json={"title": n.title, "body": n.body, "level": level, "content": f"**{n.title}**\n{n.body}"}, timeout=10)
            n.delivered_webhook = r.status_code < 400
        except httpx.HTTPError as exc:
            n.delivered_webhook = False
            log.warning("Webhook delivery failed: %s", exc.__class__.__name__)
    return n
