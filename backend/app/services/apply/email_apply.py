"""Apply by email from the owner's own mailbox (SMTP, e.g. Gmail + App Password).

Safety: only to the address stated in the listing; attachments are the generated CV/cover letter of the
latest version; a job is never emailed twice; "applied" is recorded only after the SMTP server accepts
the message. The SMTP password is stored encrypted and never logged.
"""

from __future__ import annotations

import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
MAX_ATTACHMENTS_MB = 15


@dataclass
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    from_name: str | None = None
    use_ssl: bool = True  # 465 = SSL; 587 = STARTTLS


class EmailApplyError(RuntimeError):
    pass


def read_subject_body(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    first, _, rest = text.partition("\n")
    subject = first.removeprefix("Subject:").strip()
    return subject, rest.strip()


def build_message(cfg: SmtpConfig, to: str, subject: str, body: str, attachments: list[Path]) -> EmailMessage:
    if not EMAIL_RE.match(to):
        raise EmailApplyError(f"Invalid recipient address: {to!r}")
    total = sum(p.stat().st_size for p in attachments)
    if total > MAX_ATTACHMENTS_MB * 1024 * 1024:
        raise EmailApplyError("Attachments are too large.")
    msg = EmailMessage()
    msg["From"] = formataddr((cfg.from_name or "", cfg.username))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=cfg.username.split("@")[-1])
    msg.set_content(body)
    for p in attachments:
        subtype = {"pdf": "pdf", "docx": "vnd.openxmlformats-officedocument.wordprocessingml.document"}.get(p.suffix.lstrip("."), "octet-stream")
        msg.add_attachment(p.read_bytes(), maintype="application", subtype=subtype, filename=p.name)
    return msg


def send(cfg: SmtpConfig, msg: EmailMessage, *, smtp_factory=None) -> str:
    """Send and return the Message-ID. Raises EmailApplyError on any failure (nothing is assumed sent)."""
    context = ssl.create_default_context()
    try:
        if smtp_factory is not None:
            server = smtp_factory(cfg)
        elif cfg.use_ssl:
            server = smtplib.SMTP_SSL(cfg.host, cfg.port, context=context, timeout=30)
        else:
            server = smtplib.SMTP(cfg.host, cfg.port, timeout=30)
        with server:
            if not cfg.use_ssl and smtp_factory is None:
                server.starttls(context=context)
            server.login(cfg.username, cfg.password)
            refused = server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise EmailApplyError("SMTP login failed. For Gmail use an App Password (Google Account → Security → App passwords).") from exc
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailApplyError(f"Email could not be sent: {exc.__class__.__name__}") from exc
    if refused:
        raise EmailApplyError(f"The mail server refused the recipient: {', '.join(refused)}")
    return msg["Message-ID"]
