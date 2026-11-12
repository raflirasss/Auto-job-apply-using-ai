"""Component scorers. Each returns (score 0..100, human-readable notes)."""

from __future__ import annotations

from app.schemas.settings import Preferences
from app.services.matching.candidate import CandidateFacts
from app.services.matching.location import location_matches
from app.services.matching.requirements import JobRequirements
from app.services.matching.vocab import title_categories

EDU_NAMES = {0: "unspecified", 1: "SMA/SMK", 2: "Diploma", 3: "Bachelor (S1)", 4: "Master (S2)", 5: "Doctorate"}


def score_skills(req: JobRequirements, cand: CandidateFacts) -> tuple[float, list[str], list[str]]:
    """Returns (score, matching, missing). Mandatory skills weigh double."""
    if not req.skills:
        return 50.0, [], []  # no recognisable skills: neutral, flagged as a concern elsewhere
    cand_lower = {s.lower() for s in cand.skills}
    matching = sorted(s for s in req.skills if s.lower() in cand_lower)
    missing = sorted(s for s in req.skills if s.lower() not in cand_lower)
    weight = lambda s: 2.0 if s in req.mandatory_skills else (0.5 if s in req.preferred_skills else 1.0)  # noqa: E731
    total = sum(weight(s) for s in req.skills)
    got = sum(weight(s) for s in matching)
    return round(got / total * 100, 1), matching, missing


def score_experience(req: JobRequirements, cand: CandidateFacts, job_title_cats: set[str]) -> tuple[float, list[str], list[str]]:
    """Years requirement plus relevance of past roles to the job's skills/categories."""
    notes: list[str] = []
    relevant: list[str] = []
    years = cand.total_experience_months / 12
    if req.min_years:
        years_score = min(100.0, years / req.min_years * 100)
        notes.append(f"Requires {req.min_years}+ years; profile shows about {years:.1f} years in total.")
    elif req.fresh_graduate_ok:
        years_score = 100.0
    else:
        years_score = 80.0  # no explicit requirement
    for label, text in cand.experience_texts:
        hits = [s for s in req.skills if s.lower() in text]
        if hits:
            relevant.append(f"{label}: {', '.join(sorted(hits)[:5])}")
    if req.skills:
        relevance = min(100.0, len(relevant) / max(1, len(cand.experience_texts)) * 100) if cand.experience_texts else 0.0
    else:
        relevance = 50.0
    if job_title_cats & cand.supported_categories:
        relevance = max(relevance, 70.0)
    return round(0.5 * years_score + 0.5 * relevance, 1), relevant, notes


def score_title(title: str, cand: CandidateFacts) -> tuple[float, set[str], str]:
    cats = title_categories(title)
    if not cats:
        return 30.0, cats, "Job title does not map to a known category."
    if cats & cand.selected_categories:
        return 100.0, cats, f"Title matches selected target category: {', '.join(sorted(cats & cand.selected_categories))}."
    if cats & cand.supported_categories:
        return 85.0, cats, f"Title matches a category supported by the CV: {', '.join(sorted(cats & cand.supported_categories))}."
    return 10.0, cats, f"Title category ({', '.join(sorted(cats))}) is not supported by the candidate profile."


def score_education(req: JobRequirements, cand: CandidateFacts) -> tuple[float, str]:
    if req.education_level == 0:
        return 100.0, "No education requirement detected."
    if cand.education_level >= req.education_level:
        suffix = "" if cand.education_completed else " (degree not yet completed)"
        return (100.0 if cand.education_completed else 75.0), f"Requires {EDU_NAMES[req.education_level]}; candidate has {EDU_NAMES[cand.education_level]}{suffix}."
    return 0.0, f"Requires {EDU_NAMES[req.education_level]}; candidate has {EDU_NAMES[cand.education_level]}."


def score_location(job_location: str | None, arrangement: str | None, prefs: Preferences) -> tuple[float, str]:
    loc = location_matches(job_location, prefs.location)
    arr_ok = arrangement in prefs.work_arrangement if arrangement else None
    if loc is False or arr_ok is False:
        return 0.0, "Location or work arrangement outside preferences."
    if loc is True and arr_ok is True:
        return 100.0, "Location and work arrangement match preferences."
    return 60.0, "Location or work arrangement not stated; verify on the listing."


def score_salary(job_min: float | None, job_max: float | None, disclosed: bool, minimum: int) -> tuple[float, str]:
    if not disclosed or (job_min is None and job_max is None):
        return 0.0, "Salary not disclosed; not counted as meeting the minimum."
    top = job_max if job_max is not None else job_min
    low = job_min if job_min is not None else job_max
    if low >= minimum:
        return 100.0, "Salary range meets the minimum."
    if top >= minimum:
        return 70.0, "Salary range straddles the minimum."
    return 0.0, "Salary below the minimum."
