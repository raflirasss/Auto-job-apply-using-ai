"""Polite HTTP for sources: identifies itself, honours robots.txt, spaces requests, never retries on
403/429 (a block is respected, not worked around)."""

from __future__ import annotations

import logging
import threading
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

log = logging.getLogger(__name__)
USER_AGENT = "AIJobHunter/1.0 (personal job-search assistant; single user)"
MIN_INTERVAL_S = 1.5  # per host


class Blocked(RuntimeError):
    """robots.txt disallows the URL, or the server refused (403/429)."""


class PoliteClient:
    def __init__(self, client: httpx.Client | None = None, *, respect_robots: bool = True, min_interval: float = MIN_INTERVAL_S):
        self._client = client or httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, follow_redirects=True)
        self._robots: dict[str, RobotFileParser | None] = {}
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()
        self.respect_robots = respect_robots
        self.min_interval = min_interval
        self.requests = 0

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            parser: RobotFileParser | None = RobotFileParser()
            try:
                r = self._client.get(origin + "/robots.txt")
                self.requests += 1
                if r.status_code >= 400:
                    parser = None  # no robots.txt (or unreachable): allowed by convention
                else:
                    parser.parse(r.text.splitlines())
            except httpx.HTTPError:
                parser = None
            self._robots[origin] = parser
        parser = self._robots[origin]
        return True if parser is None else parser.can_fetch(USER_AGENT, url)

    def _throttle(self, host: str) -> None:
        with self._lock:
            wait = self._last.get(host, 0) + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last[host] = time.monotonic()

    def get(self, url: str, **kwargs) -> httpx.Response:
        if not self._allowed(url):
            raise Blocked(f"robots.txt disallows {url}")
        self._throttle(urlsplit(url).netloc)
        r = self._client.get(url, **kwargs)
        self.requests += 1
        if r.status_code in (401, 403, 429):
            raise Blocked(f"{urlsplit(url).netloc} refused the request (HTTP {r.status_code})")
        r.raise_for_status()
        return r
