"""Encrypted credential storage helpers (Fernet, key derived from APP_SECRET_KEY)."""

from __future__ import annotations

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import Settings


def _fernet(settings: Settings) -> Fernet:
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ai-job-hunter",
        info=b"credential-storage-v1",
    ).derive(settings.app_secret_key.get_secret_value().encode())
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(plaintext: str, settings: Settings) -> str:
    return _fernet(settings).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(ciphertext: str, settings: Settings) -> str | None:
    try:
        return _fernet(settings).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return None


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * 8}{value[-4:]}"
