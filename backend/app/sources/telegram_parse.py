"""Turn a free-text Telegram job post into a SourceJob. Deterministic; unknown fields stay empty."""

from __future__ import annotations

import re
from datetime import datetime

from app.sources.base import SourceJob
from app.sources.text import arrangement_from, clean, work_type_from

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL = re.compile(r"https?://[^\s<>\"')]+")
JOB_WORDS = re.compile(r"(?i)\b(lowongan|loker|dibutuhkan|dicari|hiring|we are hiring|vacancy|job opening|rekrutmen|open recruitment|posisi|position)\b")
NOT_JOB = re.compile(r"(?i)\b(iklan|promo|giveaway|webinar|kursus|pelatihan berbayar|bimbel|jual|dijual)\b")
SCAM = re.compile(r"(?i)(biaya (pendaftaran|administrasi|seragam|training)|transfer (dulu|terlebih dahulu)|deposit|uang jaminan|tanpa interview langsung kerja|kerja dari hp gaji)")
POSITION = re.compile(r"(?im)^(?:posisi|position|jabatan|lowongan(?: kerja)?|dibutuhkan|dicari|hiring|we are hiring)\s*[:\-–]+\s*(.{3,90})$")
DICARI_LINE = re.compile(r"(?im)^dicari\s+(.{3,90})$")
FULL_TIME_LINE = re.compile(r"(?im)^(?:full[ -]?time|part[ -]?time)\s+(.{3,90})$")
JOB_TITLE_LINE = re.compile(r"(?im)^(?P<t>(?!!!!\s*$)[A-Za-z][A-Za-z0-9 &/().,+\-]{3,90})$")


def _title_from_body(text: str) -> str | None:
    for pattern in (POSITION, DICARI_LINE, FULL_TIME_LINE, JOB_TITLE_LINE):
        m = pattern.search(text)
        if m:
            value = clean(m.group(1) if m.lastindex else m.group("t"))
            if value and not GENERIC_HEADER.match(value) and value not in {"!!!", "-", "..."}:
                return value[:120]
    return None

COMPANY = re.compile(r"(?im)^(?:perusahaan|company|nama perusahaan)\s*[:\-–]\s*(.{2,90})$|\b(PT\.?\s+[A-Z][\w&.\- ]{2,60}|CV\.?\s+[A-Z][\w&.\- ]{2,60})")
LOCATION = re.compile(r"(?im)^(?:lokasi|location|penempatan|domisili|area)\s*[:\-–]\s*(.{2,90})$")
SALARY = re.compile(r"(?im)^.*\b(?:gaji|salary|upah|thp)\b.*$")
DEADLINE = re.compile(r"(?im)^.*\b(?:deadline|batas|paling lambat|closing)\b.*$")


def _first(pattern: re.Pattern, text: str) -> str | None:
    m = pattern.search(text)
    if not m:
        return None
    value = next((g for g in m.groups() if g), m.group(0))
    return clean(value.strip(" *_-:•"))


GENERIC_HEADER = re.compile(r"(?i)^(info )?(lowongan|loker)( kerja)?( terbaru| hari ini)?$")


def _title_line(text: str) -> str:
    """First line with real words (skips decorations like '!!!' or '🔥🔥' and generic 'LOWONGAN KERJA')."""
    for line in text.split("\n"):
        candidate = re.sub(r"[^\w&/().,+\- ]+", " ", line).strip(" .,-")
        candidate = re.sub(r"\s+", " ", candidate)
        if len(re.findall(r"[A-Za-z]", candidate)) >= 4 and not GENERIC_HEADER.match(candidate):
            return candidate[:120]
    return "Job posting"


def looks_like_job(text: str) -> bool:
    return bool(JOB_WORDS.search(text)) and not NOT_JOB.search(text[:200])


def parse_post(text: str, *, channel: str, post_id: int | str, posted_at: datetime | None) -> SourceJob | None:
    text = clean(text) or ""
    if len(text) < 40 or not looks_like_job(text):
        return None
    title = _title_from_body(text) or _title_line(text)
    emails = list(dict.fromkeys(EMAIL.findall(text)))
    urls = [u.rstrip(".,") for u in URL.findall(text) if "t.me/" not in u]
    notes = [f"From Telegram channel @{channel}."]
    if SCAM.search(text):
        notes.append("WARNING: the post asks for a fee/deposit or promises work without interview (common scam signs).")
    if deadline := _first(DEADLINE, text):
        notes.append(f"Deadline mentioned: {deadline[:80]}")
    return SourceJob(
        source="telegram", external_id=f"telegram:{channel}/{post_id}", url=f"https://t.me/{channel}/{post_id}",
        title=title[:300], company=_first(COMPANY, text), location=_first(LOCATION, text),
        work_arrangement=arrangement_from(text), employment_type=work_type_from(_first(re.compile(r"(?im)^.*\b(?:status|tipe|type|jenis)\b.*$"), text)),
        salary_label=_first(SALARY, text), description=text,
        apply_url=urls[0] if urls else None, apply_email=emails[0] if emails else None,
        posted_at=posted_at, notes=notes,
    )
