"""Page-state detection run inside the browser. Detection only: nothing here bypasses anything."""

from __future__ import annotations

import re

CAPTCHA_SELECTORS = [
    "iframe[src*='recaptcha']", "iframe[src*='hcaptcha']", "iframe[src*='turnstile']", "iframe[title*='captcha' i]",
    ".g-recaptcha", ".h-captcha", ".cf-turnstile", "[data-sitekey]", "#captcha", "[id*='captcha' i]",
]
LOGIN_SELECTORS = ["input[type=password]"]
LOGIN_TEXT = re.compile(r"(?i)\b(sign in|log ?in|masuk)\b.{0,40}\b(to (apply|continue)|untuk melamar|untuk melanjutkan)|"
                        r"\b(sign in|log in|masuk) (with|dengan) (email|google|apple|facebook)")
OTP_TEXT = re.compile(r"(?i)\b(verification code|kode verifikasi|one[- ]time (password|code)|\botp\b|verify your (identity|email|phone))")
BOT_WALL_TEXT = re.compile(r"(?i)(verify you are (a )?human|are you a robot|access denied|unusual traffic|checking your browser|just a moment)")
CLOSED_TEXT = re.compile(r"(?i)(this job (is )?(no longer|not) (available|accepting)|job (has )?expired|lowongan (ini )?(sudah )?(ditutup|tidak tersedia|kedaluwarsa)|"
                         r"no longer accepting applications|position (has been )?filled|job ad (has )?expired)")
ALREADY_APPLIED_TEXT = re.compile(r"(?i)(you('ve| have) already applied|anda sudah melamar|already applied)")
CONFIRM_TEXT = re.compile(r"(?i)(application (has been |was )?(submitted|sent|received)|thank you for (applying|your application)|"
                          r"lamaran (anda )?(telah |sudah )?(terkirim|dikirim|diterima)|terima kasih (telah|sudah) melamar|you('ve| have) applied)")
APPLY_BUTTON_TEXT = re.compile(r"(?i)^\s*(quick apply|apply now|apply|lamar cepat|lamar sekarang|lamar|kirim lamaran)\s*$")
SUBMIT_BUTTON_TEXT = re.compile(r"(?i)^\s*(submit( application)?|send( application)?|kirim( lamaran)?|ajukan( lamaran)?|apply|lamar)\s*$")


def body_text(page) -> str:
    try:
        return page.inner_text("body", timeout=5000)[:200_000]
    except Exception:
        return ""


def has_any(page, selectors: list[str]) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count() and loc.first.is_visible():
                return True
        except Exception:
            continue
    return False


def blocking_state(page) -> tuple[str, str] | None:
    """Return (stop_reason, detail) when the page requires the human; None otherwise."""
    text = body_text(page)
    if has_any(page, CAPTCHA_SELECTORS) or BOT_WALL_TEXT.search(text):
        return "captcha_or_bot_check", "CAPTCHA or anti-bot check detected. It is never bypassed; complete it manually."
    if OTP_TEXT.search(text):
        return "identity_verification", "Identity / OTP verification requested. Complete it manually."
    if has_any(page, LOGIN_SELECTORS) or LOGIN_TEXT.search(text):
        return "login_required", "Login required. Sign in yourself in the opened browser; credentials are never handled by the app."
    return None


def listing_state(page) -> str | None:
    text = body_text(page)
    if ALREADY_APPLIED_TEXT.search(text):
        return "already_applied"
    if CLOSED_TEXT.search(text):
        return "closed"
    return None


def confirmation_text(page) -> str | None:
    m = CONFIRM_TEXT.search(body_text(page))
    return m.group(0) if m else None


def find_button(page, pattern: re.Pattern[str]):
    """First visible, enabled button/link whose text matches `pattern`."""
    loc = page.locator("button, a[role=button], a, input[type=submit]")
    for i in range(min(loc.count(), 200)):
        el = loc.nth(i)
        try:
            if not el.is_visible():
                continue
            label = (el.inner_text(timeout=1000) or el.get_attribute("value") or "").strip()
            if pattern.match(label) and el.is_enabled():
                return el
        except Exception:
            continue
    return None
