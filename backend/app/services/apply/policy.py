"""Which apply methods are permitted for a job.

  * email    - listing says "send your CV to <address>": sent from the owner's own mailbox (SMTP) with the
               generated CV and cover letter. Fully automatic.
  * auto     - unattended browser submission on the employer's own application form (e.g. Lever/Greenhouse
               hosted forms). Stops on CAPTCHA, login, sensitive or unknown questions.
  * assisted - visible browser, verified fields pre-filled, the owner reviews and submits.
"""

from __future__ import annotations

from urllib.parse import urlsplit

# Hosts whose application pages block automation; never auto-submit there.
AUTO_SUBMIT_BLOCKED_HOSTS = ("jobstreet.com", "linkedin.com", "indeed.com", "glints.com")
# Hosts that are posts/aggregators, not application forms (Telegram posts, Google redirect links).
NOT_A_FORM_HOSTS = ("t.me", "telegram.me", "google.com")


def _host(url: str | None) -> str:
    return (urlsplit(url).hostname or "").lower() if url else ""


def _matches(host: str, hosts: tuple[str, ...]) -> bool:
    return any(host == h or host.endswith("." + h) for h in hosts)


def allowed_modes(url: str | None, apply_email: str | None = None) -> list[str]:
    modes: list[str] = []
    if apply_email:
        modes.append("email")
    host = _host(url)
    if host and not _matches(host, NOT_A_FORM_HOSTS):
        modes.append("assisted")
        if not _matches(host, AUTO_SUBMIT_BLOCKED_HOSTS):
            modes.append("auto")
    return modes


def policy_note(url: str | None, apply_email: str | None = None) -> str:
    modes = allowed_modes(url, apply_email)
    if not modes:
        return "No application method found in this listing. Open the link and apply as the post describes."
    parts = []
    if "email" in modes:
        parts.append(f"Email: sent from your mailbox to {apply_email}.")
    if "auto" in modes:
        parts.append("Auto: the browser fills and submits the employer's form, stopping on anything unverified.")
    elif "assisted" in modes:
        parts.append("Assisted only: this site blocks automated submission; you click submit.")
    return " ".join(parts)
