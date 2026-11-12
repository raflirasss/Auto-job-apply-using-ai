"""Dashboard authentication: single-owner password login with signed session tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings

SESSION_COOKIE = "ajh_session"


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _signing_key(settings: Settings) -> bytes:
    return hashlib.sha256(b"session-signing:" + settings.app_secret_key.get_secret_value().encode()).digest()


def create_session_token(settings: Settings, now: float | None = None) -> str:
    issued = int(now if now is not None else time.time())
    payload = {"sub": "owner", "iat": issued, "exp": issued + settings.session_ttl_hours * 3600}
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(_signing_key(settings), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_session_token(token: str, settings: Settings, now: float | None = None) -> dict | None:
    try:
        body, sig = token.split(".", 1)
        expected = _b64e(hmac.new(_signing_key(settings), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64d(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("sub") != "owner" or int(payload.get("exp", 0)) < (now if now is not None else time.time()):
        return None
    return payload


def check_password(candidate: str, settings: Settings) -> bool:
    return hmac.compare_digest(
        candidate.encode("utf-8"), settings.dashboard_password.get_secret_value().encode("utf-8")
    )


@dataclass
class LoginThrottle:
    """In-memory brute-force protection: lock a client after repeated failures."""

    max_failures: int = 5
    lockout_seconds: int = 300
    _failures: dict[str, list[float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def is_locked(self, client: str, now: float | None = None) -> bool:
        now = now or time.time()
        with self._lock:
            recent = [t for t in self._failures.get(client, []) if now - t < self.lockout_seconds]
            self._failures[client] = recent
            return len(recent) >= self.max_failures

    def record_failure(self, client: str, now: float | None = None) -> None:
        with self._lock:
            self._failures.setdefault(client, []).append(now or time.time())

    def reset(self, client: str) -> None:
        with self._lock:
            self._failures.pop(client, None)


login_throttle = LoginThrottle()


def require_auth(request: Request, settings: Settings = Depends(get_settings)) -> dict:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
    payload = verify_session_token(token, settings) if token else None
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return payload
