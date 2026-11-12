"""Text helpers shared by all sources: HTML -> text, salary labels, work type, arrangement."""

from __future__ import annotations

import html as htmllib
import re
from dataclasses import dataclass

import lxml.html

_BLOCK_TAGS = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "ul", "ol", "section"}


def clean(text: str | None) -> str | None:
    if text is None:
        return None
    lines = [re.sub(r"[ \t\u00a0]+", " ", ln).strip() for ln in str(text).replace("\r", "").split("\n")]
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return out or None


def html_to_text(fragment: str | None) -> str | None:
    """HTML (possibly entity-escaped, as in Greenhouse) -> plain text with line breaks and bullets."""
    if not fragment or not fragment.strip():
        return None
    if "&lt;" in fragment and "<" not in fragment:
        fragment = htmllib.unescape(fragment)
    if "<" not in fragment:
        return clean(htmllib.unescape(fragment))
    try:
        root = lxml.html.fragment_fromstring(fragment, create_parent="div")
    except Exception:
        return clean(re.sub(r"<[^>]+>", " ", fragment))
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        if tag in {"script", "style"}:
            el.drop_tree() if el.getparent() is not None else None
            continue
        if tag == "li":
            el.text = "• " + (el.text or "")
        if tag in _BLOCK_TAGS:
            el.tail = "\n" + (el.tail or "")
    return clean(root.text_content())


# ---------------- salary ----------------

_PERIODS = [
    ("annual", r"(?:\bper ?|/ ?)(?:year|yr|annum|thn|tahun)\b|\b(?:annually|yearly|setahun|tahunan)\b"),
    ("monthly", r"(?:\bper ?|/ ?)(?:month|mo|bln|bulan)\b|\b(?:monthly|sebulan|bulanan)\b"),
    ("weekly", r"(?:\bper ?|/ ?)(?:week|minggu)\b|\b(?:weekly|mingguan)\b"),
    ("daily", r"(?:\bper ?|/ ?)(?:day|hari)\b|\b(?:daily|harian)\b"),
    ("hourly", r"(?:\bper ?|/ ?)(?:hour|hr|jam)\b|\bhourly\b"),
]
_IDR = re.compile(r"(?i)(\bRp\.?|\bIDR\b)")
_JUTA = re.compile(r"(?i)\d\s*(jt|juta)\b")
_OTHER_CURRENCY = re.compile(r"(?i)([$€£¥]|\b(USD|SGD|MYR|AUD|EUR|GBP|RM)\b)")
_NUM = re.compile(r"(?i)(\d+(?:[.,]\d+)*)\s*(jt|juta|million|mn|m|rb|ribu|k)?\b")


def _to_number(raw: str, suffix: str | None) -> float:
    groups = re.split(r"[.,]", raw)
    if len(groups) > 1 and all(len(g) == 3 for g in groups[1:]) and not (suffix and len(groups) == 2):
        value = float("".join(groups))
    elif len(groups) > 1:
        value = float("".join(groups[:-1]) + "." + groups[-1])
    else:
        value = float(raw)
    mult = {"jt": 1e6, "juta": 1e6, "million": 1e6, "mn": 1e6, "m": 1e6, "rb": 1e3, "ribu": 1e3, "k": 1e3}
    return value * mult.get((suffix or "").lower(), 1)


@dataclass
class ParsedSalary:
    disclosed: bool
    min_value: float | None = None
    max_value: float | None = None
    period: str = "monthly"
    note: str | None = None


def parse_salary_label(label: str | None) -> ParsedSalary:
    """'Rp 5.000.000 – Rp 7.000.000 per month' / 'Gaji 4,5 - 5 jt' -> range. Ambiguous -> undisclosed.

    An amount written in "jt/juta" without a period is read as monthly IDR (the standard way Indonesian
    job posts state salary); that assumption is recorded in `note`.
    """
    if not label or not label.strip():
        return ParsedSalary(False, note="no salary shown")
    text = label.strip()
    if _OTHER_CURRENCY.search(text):
        return ParsedSalary(False, note=f"salary not in IDR: {text}")
    has_idr, has_juta = bool(_IDR.search(text)), bool(_JUTA.search(text))
    if not (has_idr or has_juta):
        return ParsedSalary(False, note=f"salary currency unclear: {text}")
    period = next((name for name, pat in _PERIODS if re.search(pat, text, re.I)), None)
    note = None
    if period is None:
        if not has_juta:
            return ParsedSalary(False, note=f"salary period not stated: {text}")
        period, note = "monthly", "period not stated; 'jt' amount read as monthly IDR"
    if period == "hourly":
        return ParsedSalary(False, note=f"hourly salary not converted: {text}")
    raw = _NUM.findall(text)
    # "4,5 - 5,5 jt": the unit is written once but applies to the whole range.
    suffixes = [s for _, s in raw if s]
    shared = suffixes[-1] if len(set(s.lower() for s in suffixes)) == 1 else None
    numbers = [_to_number(a, s or (shared if len(raw) == 2 else None)) for a, s in raw]
    numbers = [n for n in numbers if n >= 1000]
    if not numbers:
        return ParsedSalary(False, note=f"salary not numeric: {text}")
    lo = numbers[0]
    hi = numbers[1] if len(numbers) > 1 else lo
    if hi < lo:
        lo, hi = hi, lo
    return ParsedSalary(True, lo, hi, period, note)


# ---------------- work type / arrangement ----------------

_WORK_TYPES = [
    ("contract", "contract"), ("kontrak", "contract"), ("pkwt", "contract"), ("full", "full_time"),
    ("penuh waktu", "full_time"), ("permanent", "full_time"), ("tetap", "full_time"), ("part", "part_time"),
    ("paruh waktu", "part_time"), ("intern", "internship"), ("magang", "internship"), ("freelance", "freelance"),
    ("temp", "temporary"), ("casual", "temporary"),
]
_LD_WORK_TYPES = {"FULL_TIME": "full_time", "PART_TIME": "part_time", "CONTRACTOR": "contract",
                  "TEMPORARY": "temporary", "INTERN": "internship", "PER_DIEM": "temporary"}


def work_type_from(text: str | None) -> str | None:
    if not text:
        return None
    if text.strip().upper() in _LD_WORK_TYPES:
        return _LD_WORK_TYPES[text.strip().upper()]
    lower = text.lower()
    return next((v for k, v in _WORK_TYPES if k in lower), None)


def arrangement_from(text: str | None) -> str | None:
    if not text:
        return None
    lower = text.lower()
    if re.search(r"\bhybrid\b|\bhibrida\b", lower):
        return "hybrid"
    if re.search(r"\bremote\b|jarak jauh|\btelecommute\b|work from home|\bwfh\b", lower):
        return "remote"
    if re.search(r"on-?site|\bin[- ]office\b|\bwfo\b|\bdi kantor\b", lower):
        return "onsite"
    return None
