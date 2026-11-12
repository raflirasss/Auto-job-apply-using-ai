"""Low-level helpers for the CV parser: headings, dates, contact info, list splitting."""

from __future__ import annotations

import re
from datetime import date

from app.services.cv_text import Line

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("profile", "summary", "professional summary", "about me", "profil", "ringkasan", "objective"),
    "education": ("education", "pendidikan", "academic background"),
    "experience": (
        "work experience", "experience", "professional experience", "employment history",
        "pengalaman kerja", "pengalaman", "internship experience",
    ),
    "skills": ("skill", "skills", "technical skills", "keahlian", "kemampuan", "core competencies"),
    "languages": ("languages", "language", "bahasa"),
    "certifications": ("certifications", "certification", "certificates", "licenses & certifications", "sertifikasi"),
    "projects": ("projects", "project", "proyek", "portfolio projects"),
    "achievements": ("achievements", "awards", "honors", "prestasi", "penghargaan"),
    "organizations": ("organizations", "organization", "organisasi", "volunteer", "leadership"),
}
_HEADING_LOOKUP = {alias: key for key, aliases in SECTION_ALIASES.items() for alias in aliases}

_MONTH_GROUPS = [
    ("jan", "january", "januari"), ("feb", "february", "februari"), ("mar", "march", "maret"),
    ("apr", "april"), ("may", "mei"), ("jun", "june", "juni"), ("jul", "july", "juli"),
    ("aug", "august", "agu", "agustus", "agt"), ("sep", "sept", "september"),
    ("oct", "october", "okt", "oktober"), ("nov", "november", "nop", "nopember"),
    ("dec", "december", "des", "desember"),
]
MONTHS = {name: i + 1 for i, names in enumerate(_MONTH_GROUPS) for name in names}
_MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
_DATE_TOKEN = rf"(?:(?:{_MONTH_RE})\.?\s+)?(?:19|20)\d{{2}}"
PRESENT_RE = r"present|current|now|sekarang|saat ini"
DATE_RANGE_RE = re.compile(
    rf"(?i)^\s*(?P<start>{_DATE_TOKEN})\s*(?:-|–|—|to|s/d|sampai)\s*(?P<end>{_DATE_TOKEN}|{PRESENT_RE})\s*$"
)
SINGLE_DATE_RE = re.compile(rf"(?i)^\s*{_DATE_TOKEN}\s*$")

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:\+62|62|0)[\s-]?8\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,5}")
URL_RE = re.compile(
    r"(?i)\b(?:https?://)?(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*"
    r"\.(?:com|id|io|app|dev|me|net|org|co|site|xyz)(?:/[^\s|]*)?"
)
GPA_RE = re.compile(
    r"(?i)(?:gpa|ipk)\s*[:\-]?\s*(?P<gpa>\d(?:[.,]\d{1,2})?)\s*(?:/\s*(?P<scale>\d(?:[.,]\d{1,2})?))?"
)
DEGREE_RE = re.compile(
    r"(?i)^(?P<degree>bachelor(?:'s)?(?: degree)?|master(?:'s)?(?: degree)?|diploma(?: [ivx\d]+)?|d[1-4]|s[1-3]|"
    r"sarjana|associate(?: degree)?|doctor(?:ate)?|ph\.?d\.?|high school|sma|smk|vocational)"
    r"(?:\s+(?:of|in|degree in|-|,)\s*(?P<field>.+))?$"
)
SOFT_SKILL_TERMS = (
    "detail oriented", "detail-oriented", "adaptable", "fast-learning", "fast learner", "team player",
    "problem solving", "problem-solving", "time management", "teamwork", "self-motivated",
    "proactive", "collaborative",
)
LANGUAGE_CATEGORY_RE = re.compile(r"(?i)^(languages?|bahasa)$")
LANGUAGE_ITEM_RE = re.compile(r"^(?P<name>[^()]+?)\s*(?:\((?P<level>[^)]+)\))?$")


def heading_key(line: Line) -> str | None:
    if len(line.text) > 40:
        return None
    key = _HEADING_LOOKUP.get(re.sub(r"[^a-z &]", "", line.text.lower()).strip())
    if key and (line.is_bold or line.text.isupper()):
        return key
    return None


def is_right_column(line: Line) -> bool:
    return line.x0 > line.page_width * 0.55


def parse_date(token: str) -> str | None:
    token = token.strip().rstrip(".")
    m = re.match(rf"(?i)^(?:(?P<mon>{_MONTH_RE})\.?\s+)?(?P<year>(?:19|20)\d{{2}})$", token)
    if not m:
        return None
    mon = m.group("mon")
    return f"{m.group('year')}-{MONTHS[mon.lower()]:02d}" if mon else m.group("year")


def parse_date_range(text: str) -> tuple[str | None, str | None, bool] | None:
    """Return (start, end, is_present) or None if `text` is not a date/date range."""
    m = DATE_RANGE_RE.match(text)
    if m:
        end_raw = m.group("end").strip()
        present = bool(re.fullmatch(rf"(?i){PRESENT_RE}", end_raw))
        return parse_date(m.group("start")), (None if present else parse_date(end_raw)), present
    if SINGLE_DATE_RE.match(text):
        d = parse_date(text)
        return d, d, False
    return None


def date_is_future(value: str | None, today: date) -> bool:
    if not value:
        return False
    parts = value.split("-")
    month = int(parts[1]) if len(parts) > 1 else 12
    return (int(parts[0]), month) > (today.year, today.month)


def join_wrapped(lines: list[Line]) -> list[str]:
    """Merge visually wrapped lines into logical items."""
    items: list[str] = []
    for line in lines:
        text = line.text
        continues = items and not line.is_bullet and (
            text[:1].islower() or items[-1].endswith((",", "&", "-", " and", " or"))
        )
        if continues:
            items[-1] = f"{items[-1]} {text}"
        else:
            items.append(text)
    return items


def split_list(text: str) -> list[str]:
    return [p.strip(" .") for p in re.split(r",|;|\u2022|\|", text) if p.strip(" .")]
