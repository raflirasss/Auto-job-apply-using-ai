"""Telegram job channels.

Two read-only access methods for *public* channels the owner chooses:
  * "api"     - official Telegram API (MTProto via Telethon) with the owner's own api_id/api_hash and a
                session the owner authorises once. Recommended: full history, no HTML parsing.
  * "preview" - Telegram's public web preview https://t.me/s/<channel> (served to every visitor).
Nothing posts, joins, or messages anyone. Requests are spaced to stay far from flood limits.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone

import lxml.html

from app.sources.base import FetchContext, FetchResult, JobSourceAdapter, SourceUnavailableError
from app.sources.http import Blocked, PoliteClient
from app.sources.telegram_parse import parse_post
from app.sources.text import clean

CHANNEL = re.compile(r"^(?:https?://t\.me/(?:s/)?)?@?([A-Za-z0-9_]{4,64})/?$")


def channel_name(value: str) -> str | None:
    m = CHANNEL.match((value or "").strip())
    return m.group(1) if m else None


def parse_preview(html: str, channel: str) -> list[tuple[str, int, datetime | None]]:
    """t.me/s/<channel> HTML -> [(text, post_id, datetime)]."""
    root = lxml.html.fromstring(html)
    out = []
    for msg in root.xpath('//div[contains(@class,"tgme_widget_message ") and @data-post]'):
        post = msg.get("data-post", "")
        if not post.lower().startswith(channel.lower() + "/"):
            continue
        texts = msg.xpath('.//div[contains(@class,"tgme_widget_message_text")]')
        if not texts:
            continue
        for br in texts[0].iter("br"):
            br.tail = "\n" + (br.tail or "")
        times = msg.xpath(".//time/@datetime")
        when = datetime.fromisoformat(times[0]) if times else None
        out.append((clean(texts[0].text_content()) or "", int(post.split("/")[-1]), when))
    return out


async def _api_messages(cfg: dict, channels: list[str], since: datetime, limit: int):
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    client = TelegramClient(StringSession(cfg["session"]), int(cfg["api_id"]), cfg["api_hash"],
                            flood_sleep_threshold=60, receive_updates=False)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise SourceUnavailableError("Telegram session is not authorised. Connect Telegram in Settings → Sources.")
        result = {}
        for ch in channels:
            msgs = []
            async for m in client.iter_messages(ch, limit=limit):
                if m.date and m.date < since:
                    break
                if m.message:
                    msgs.append((m.message, m.id, m.date))
            result[ch] = msgs
            await asyncio.sleep(2)  # gentle pacing between channels
        return result
    finally:
        await client.disconnect()


class TelegramAdapter(JobSourceAdapter):
    name = "telegram"
    label = "Telegram job channels"

    def __init__(self, client_factory=PoliteClient, api_reader=None):
        self._client_factory = client_factory
        self._api_reader = api_reader or (lambda cfg, chs, since, lim: asyncio.run(_api_messages(cfg, chs, since, lim)))

    def fetch(self, config: dict, ctx: FetchContext) -> FetchResult:
        result = FetchResult()
        channels = [c for c in (channel_name(x) for x in config.get("channels", [])) if c]
        if not channels:
            result.notes.append("No Telegram channels configured.")
            return result
        since = datetime.now(timezone.utc) - timedelta(days=ctx.lookback_days)
        per_channel = int(config.get("messages_per_channel", 100))
        api_ready = all(config.get(k) for k in ("api_id", "api_hash", "session"))

        posts: dict[str, list] = {}
        if config.get("method", "api") == "api" and api_ready:
            try:
                posts = self._api_reader(config, channels, since, per_channel)
            except SourceUnavailableError as exc:
                result.errors.append(str(exc))
            except Exception as exc:
                result.errors.append(f"Telegram API: {exc.__class__.__name__}: {str(exc)[:200]}")
        else:
            if config.get("method", "api") == "api":
                result.notes.append("Telegram API not connected; using the public channel preview (t.me/s/…).")
            with self._client_factory() as http:
                for ch in channels:
                    try:
                        posts[ch] = parse_preview(http.get(f"https://t.me/s/{ch}").text, ch)
                    except Blocked as exc:
                        result.errors.append(f"@{ch}: {exc}")
                    except Exception as exc:
                        result.errors.append(f"@{ch}: {exc.__class__.__name__}")
                result.requests = http.requests

        for ch, items in posts.items():
            kept = 0
            for text, post_id, when in items:
                if when and when < since:
                    continue
                job = parse_post(text, channel=ch, post_id=post_id, posted_at=when)
                if job:
                    result.jobs.append(job)
                    kept += 1
            if not items:
                result.notes.append(f"@{ch}: no recent posts (channel may be private, empty, or inactive).")
            elif not kept:
                result.notes.append(f"@{ch}: {len(items)} recent post(s), none looked like a job listing.")
        result.jobs = result.jobs[: ctx.max_items]
        return result
