"""One-time Telegram login for the owner's own account (official API). Produces a session string that is
stored encrypted. The login code / 2FA password are used once and never stored."""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass

PENDING_TTL_S = 10 * 60


class TelegramLoginError(RuntimeError):
    pass


@dataclass
class _Pending:
    api_id: int
    api_hash: str
    phone: str
    phone_code_hash: str
    session: str
    created: float


_pending: _Pending | None = None
_lock = threading.Lock()


async def _send_code(api_id: int, api_hash: str, phone: str) -> tuple[str, str]:
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    try:
        sent = await client.send_code_request(phone)
        return sent.phone_code_hash, client.session.save()
    finally:
        await client.disconnect()


async def _sign_in(p: _Pending, code: str, password: str | None) -> str:
    from telethon import TelegramClient
    from telethon.errors import PhoneCodeExpiredError, PhoneCodeInvalidError, SessionPasswordNeededError
    from telethon.sessions import StringSession

    client = TelegramClient(StringSession(p.session), p.api_id, p.api_hash)
    await client.connect()
    try:
        try:
            await client.sign_in(phone=p.phone, code=code, phone_code_hash=p.phone_code_hash)
        except SessionPasswordNeededError:
            if not password:
                raise TelegramLoginError("This account has two-step verification. Enter your Telegram password too.")
            await client.sign_in(password=password)
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as exc:
            raise TelegramLoginError("The code is invalid or expired. Request a new code.") from exc
        return client.session.save()
    finally:
        await client.disconnect()


def send_code(api_id: int, api_hash: str, phone: str) -> None:
    global _pending
    try:
        code_hash, session = asyncio.run(_send_code(api_id, api_hash, phone))
    except Exception as exc:
        raise TelegramLoginError(f"Could not request a code: {exc.__class__.__name__}: {str(exc)[:150]}") from exc
    with _lock:
        _pending = _Pending(api_id, api_hash, phone, code_hash, session, time.time())


def verify(code: str, password: str | None) -> tuple[int, str, str]:
    """Returns (api_id, api_hash, session_string)."""
    global _pending
    with _lock:
        p = _pending
    if p is None or time.time() - p.created > PENDING_TTL_S:
        raise TelegramLoginError("No pending login. Request a code first.")
    try:
        session = asyncio.run(_sign_in(p, code.strip(), password))
    except TelegramLoginError:
        raise
    except Exception as exc:
        raise TelegramLoginError(f"Login failed: {exc.__class__.__name__}: {str(exc)[:150]}") from exc
    with _lock:
        _pending = None
    return p.api_id, p.api_hash, session
