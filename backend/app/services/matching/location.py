"""Location normalisation for Greater Jakarta (English/Indonesian names, common abbreviations)."""

from __future__ import annotations

import re

_REPLACEMENTS: list[tuple[str, str]] = [
    (r"\bsouth jakarta\b|\bjaksel\b", "jakarta selatan"),
    (r"\bcentral jakarta\b|\bjakpus\b", "jakarta pusat"),
    (r"\bwest jakarta\b|\bjakbar\b", "jakarta barat"),
    (r"\beast jakarta\b|\bjaktim\b", "jakarta timur"),
    (r"\bnorth jakarta\b|\bjakut\b", "jakarta utara"),
    (r"\bsouth tangerang\b|\btangsel\b|\bbsd( city)?\b|\bserpong\b|\bbintaro\b", "tangerang selatan"),
    (r"\bdki jakarta\b|\bjakarta raya\b|\bgreater jakarta\b", "jakarta"),
    (r"\bcikarang\b", "bekasi"),
    (r"\b(scbd|sudirman|kuningan|kebayoran)\b", "jakarta selatan"),
]
_NOISE = re.compile(r"\b(kota|kabupaten|kab\.?|city|regency|indonesia|banten|jawa barat|west java|provinsi|province)\b")


def normalize_location(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    text = value.lower()
    for pattern, repl in _REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    text = _NOISE.sub(" ", text)
    text = re.sub(r"[^a-z ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _contains_phrase(haystack: str, needle: str) -> bool:
    return bool(re.search(rf"(?<![a-z]){re.escape(needle)}(?![a-z])", haystack))


def location_matches(job_location: str | None, accepted: list[str]) -> bool | None:
    """True if accepted, False if clearly outside, None if the job location is unknown."""
    job = normalize_location(job_location)
    if job is None:
        return None
    for pref in accepted:
        p = normalize_location(pref)
        if p and (_contains_phrase(job, p) or _contains_phrase(p, job)):
            return True
    return False
