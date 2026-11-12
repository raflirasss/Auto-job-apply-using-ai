"""Deterministic requirement extraction from job descriptions (English + Indonesian)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services.matching.vocab import extract_skills

# Education levels: 0 unknown/none, 1 SMA/SMK, 2 diploma, 3 bachelor, 4 master, 5 doctorate.
EDU_PATTERNS: list[tuple[int, str]] = [
    (5, r"\b(ph\.?d|doctorate|doktor|s3)\b"),
    (4, r"\b(master'?s?|magister|s2|mba)\b"),
    (3, r"\b(bachelor'?s?|sarjana|s1|undergraduate|university degree)\b"),
    (2, r"\b(diploma|d3|d-3|diii|d4|associate degree)\b"),
    (1, r"\b(sma|smk|high school|senior high|slta)\b"),
]
MANDATORY_CUE = re.compile(r"(?i)\b(must|required|requirement|wajib|harus|mandatory|mampu|menguasai|proficient|minimum|minimal|min\.)\b")
OPTIONAL_CUE = re.compile(r"(?i)\b(preferred|nice to have|plus|advantage|diutamakan|nilai tambah|lebih disukai|bonus)\b")
YEARS_RE = re.compile(
    r"(?i)(?:min(?:imum|imal)?\.?\s*)?(\d{1,2})\s*(?:\+|-\s*\d{1,2})?\s*(?:years?|yrs?|tahun|thn)\b"
    r"(?=[^.\n]{0,40}(?:experience|pengalaman|exp\b|di bidang|in\b))"
)
FRESH_GRAD_RE = re.compile(r"(?i)\b(fresh ?grad(uate)?s?|lulusan baru|no experience required|tanpa pengalaman|fresh graduates? (are )?welcome)\b")
REMOTE_RE = re.compile(r"(?i)\b(fully remote|100% remote|remote only|work from anywhere|wfa|full remote)\b")
HYBRID_RE = re.compile(r"(?i)\b(hybrid|wfo ?/ ?wfh|wfh ?/ ?wfo)\b")


@dataclass
class JobRequirements:
    skills: set[str] = field(default_factory=set)
    mandatory_skills: set[str] = field(default_factory=set)
    preferred_skills: set[str] = field(default_factory=set)
    min_years: int | None = None
    education_level: int = 0
    education_mandatory: bool = False
    fresh_graduate_ok: bool = False
    remote_signal: bool = False
    hybrid_signal: bool = False


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?:\n+|(?<=[.;])\s+|\s[•\-–*]\s)", text)
    return [p.strip() for p in parts if p and p.strip()]


def education_level_of(text: str) -> int:
    lower = text.lower()
    for level, pattern in EDU_PATTERNS:
        if re.search(pattern, lower):
            return level
    return 0


def extract_requirements(title: str, description: str | None) -> JobRequirements:
    text = f"{title}\n{description or ''}"
    req = JobRequirements(skills=extract_skills(text))
    for sentence in _sentences(description or ""):
        found = extract_skills(sentence)
        if not found:
            continue
        if OPTIONAL_CUE.search(sentence):
            req.preferred_skills |= found
        elif MANDATORY_CUE.search(sentence):
            req.mandatory_skills |= found
    req.preferred_skills -= req.mandatory_skills

    years = [int(m.group(1)) for m in YEARS_RE.finditer(text) if 0 < int(m.group(1)) <= 20]
    req.min_years = min(years) if years else None
    req.fresh_graduate_ok = bool(FRESH_GRAD_RE.search(text))

    # Education: the lowest level mentioned is the minimum ("S1/D3" -> D3).
    levels = [lvl for lvl, pattern in EDU_PATTERNS if re.search(pattern, text.lower())]
    if levels:
        req.education_level = min(levels)
        req.education_mandatory = any(
            MANDATORY_CUE.search(s) and education_level_of(s) for s in _sentences(description or "")
        )
    req.remote_signal = bool(REMOTE_RE.search(text))
    req.hybrid_signal = bool(HYBRID_RE.search(text))
    return req
