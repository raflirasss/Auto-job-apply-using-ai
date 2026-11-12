"""Facts derived from the candidate profile for matching (skills, months of experience, education)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.schemas.candidate import CandidateProfileData
from app.services.categories import category_evidence, profile_text
from app.services.matching.requirements import education_level_of
from app.services.matching.vocab import extract_skills


@dataclass
class CandidateFacts:
    skills: set[str]
    total_experience_months: int
    experience_dates_known: bool
    education_level: int
    education_completed: bool
    supported_categories: set[str]
    selected_categories: set[str]
    experience_texts: list[tuple[str, str]] = field(default_factory=list)  # (label, lowercase text)


def _to_ym(value: str | None, end: bool, today: date) -> tuple[int, int] | None:
    if not value:
        return None
    if value.strip().lower() in {"present", "now", "current", "sekarang"}:
        return today.year, today.month
    parts = value.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else (12 if end else 1)
    except ValueError:
        return None
    return year, month


def experience_months(profile: CandidateProfileData, today: date) -> tuple[int, bool]:
    """Sum of role durations (overlaps merged). Year-only dates count Jan..Dec (inclusive)."""
    spans: list[tuple[int, int]] = []
    all_known = True
    for exp in profile.experience:
        start = _to_ym(exp.start_date, False, today)
        end = _to_ym(exp.end_date, True, today)
        if not start or not end:
            all_known = False
            continue
        a, b = start[0] * 12 + start[1] - 1, end[0] * 12 + end[1] - 1
        if b >= a:
            spans.append((a, b))
    spans.sort()
    total, cur = 0, None
    for a, b in spans:
        if cur and a <= cur[1] + 1:
            cur = (cur[0], max(cur[1], b))
        else:
            if cur:
                total += cur[1] - cur[0] + 1
            cur = (a, b)
    if cur:
        total += cur[1] - cur[0] + 1
    return total, all_known


def build_candidate_facts(profile: CandidateProfileData, today: date | None = None) -> CandidateFacts:
    today = today or date.today()
    skills = extract_skills(profile_text(profile))
    for group in profile.skills:  # explicit skills count even when not in the vocabulary
        skills |= {s for s in group.skills if s}
    if any(lang.name.lower() in {"english", "bahasa inggris"} for lang in profile.languages):
        skills.add("English")

    edu_level, completed = 0, False
    for edu in profile.education:
        level = education_level_of(f"{edu.degree or ''} {edu.field_of_study or ''}")
        if level > edu_level:
            edu_level, completed = level, not edu.is_expected

    months, known = experience_months(profile, today)
    evidence = category_evidence(profile)
    texts = [
        (f"{e.title or 'Role'} at {e.company}", " ".join([e.title or "", *e.responsibilities]).lower())
        for e in profile.experience
    ]
    return CandidateFacts(
        skills=skills,
        total_experience_months=months,
        experience_dates_known=known,
        education_level=edu_level,
        education_completed=completed,
        supported_categories={c["category"] for c in evidence if c["supported"]},
        selected_categories=set(profile.target_job_categories),
        experience_texts=texts,
    )
