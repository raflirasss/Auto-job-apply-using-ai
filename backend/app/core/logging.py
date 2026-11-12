"""Logging setup with redaction of personal data and secrets."""

from __future__ import annotations

import logging
import re

_REDACTIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    (re.compile(r"(?<!\w)\+?\d[\d\s().-]{8,}\d(?!\w)"), "[phone]"),
    (re.compile(r"(?i)(password|passwd|api[_-]?key|secret|token|authorization)(\s*[=:]\s*)\S+"), r"\1\2[redacted]"),
    (re.compile(r"(?i)bearer\s+[\w.\-]+"), "Bearer [redacted]"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{8,}"), "[api-key]"),
]


def redact(text: str) -> str:
    for pattern, repl in _REDACTIONS:
        text = pattern.sub(repl, text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - defensive
            return True
        record.msg = redact(message)
        record.args = None
        return True


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if not any(isinstance(f, RedactingFilter) for h in root.handlers for f in h.filters):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handler.addFilter(RedactingFilter())
        root.addHandler(handler)
    root.setLevel(level)
