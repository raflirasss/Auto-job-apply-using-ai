"""Matching engine: weighted score + hard filters + recommendation. Pure function, no I/O."""

from __future__ import annotations

from datetime import date

from app.schemas.candidate import CandidateProfileData
from app.schemas.settings import Preferences
from app.services.matching import scoring
from app.services.matching.candidate import build_candidate_facts
from app.services.matching.filters import concerns as find_concerns
from app.services.matching.filters import hard_filters, salary_unknown
from app.services.matching.requirements import extract_requirements

ENGINE_VERSION = "1.0"
WEIGHTS = {"skills": 0.35, "experience": 0.25, "title": 0.15, "education": 0.10, "location": 0.10, "salary": 0.05}


def _recommend(score: float, hard: list[dict], blocks_auto: bool, sal_unknown: bool, prefs: Preferences) -> tuple[str, str]:
    """Returns (recommendation, suggested application status)."""
    if hard:
        return "reject", "rejected"
    if score >= prefs.minimum_match_score and not blocks_auto:
        return "auto_apply_eligible", "qualified"
    if score >= prefs.review_threshold:
        if sal_unknown and not prefs.allow_undisclosed_salary_review:
            return "skip", "analyzed"
        return "review", "analyzed"
    return "skip", "analyzed"


def evaluate(job, profile: CandidateProfileData, prefs: Preferences, *, today: date | None = None, duplicate_application: bool = False) -> dict:
    """`job` is any object exposing the Job model attributes."""
    req = extract_requirements(job.title, job.description)
    cand = build_candidate_facts(profile, today)

    skills, matching, missing = scoring.score_skills(req, cand)
    title_score, title_cats, title_note = scoring.score_title(job.title, cand)
    exp, relevant, exp_notes = scoring.score_experience(req, cand, title_cats)
    edu, edu_note = scoring.score_education(req, cand)
    arrangement = job.work_arrangement or ("remote" if req.remote_signal else ("hybrid" if req.hybrid_signal else None))
    loc, loc_note = scoring.score_location(job.location, arrangement, prefs)
    sal, sal_note = scoring.score_salary(job.salary_min_monthly, job.salary_max_monthly, job.salary_disclosed, prefs.minimum_salary)

    components = {
        "skills": {"score": skills, "weight": WEIGHTS["skills"], "note": f"{len(matching)} of {len(req.skills)} detected skills matched."},
        "experience": {"score": exp, "weight": WEIGHTS["experience"], "note": " ".join(exp_notes) or "Relevance assessed from past roles."},
        "title": {"score": title_score, "weight": WEIGHTS["title"], "note": title_note},
        "education": {"score": edu, "weight": WEIGHTS["education"], "note": edu_note},
        "location": {"score": loc, "weight": WEIGHTS["location"], "note": loc_note},
        "salary": {"score": sal, "weight": WEIGHTS["salary"], "note": sal_note},
    }
    score = round(sum(c["score"] * c["weight"] for c in components.values()), 1)

    hard = hard_filters(
        job, req, cand, prefs, arrangement=arrangement, title_cats=title_cats, title_score=title_score,
        edu_note=edu_note, title_note=title_note, duplicate_application=duplicate_application,
    )
    warn = find_concerns(job, req, cand, arrangement)
    sal_unknown = salary_unknown(job)
    # Unverified salary/location/arrangement can never be auto-applied; they go to review.
    blocks_auto = sal_unknown or job.location is None or arrangement is None
    recommendation, status = _recommend(score, hard, blocks_auto, sal_unknown, prefs)

    return {
        "engine_version": ENGINE_VERSION,
        "score": score,
        "components": components,
        "matching_skills": matching,
        "missing_skills": missing,
        "mandatory_skills": sorted(req.mandatory_skills),
        "relevant_experience": relevant,
        "concerns": warn,
        "hard_filter_failures": hard,
        "passed_hard_filters": not hard,
        "salary": {
            "disclosed": not sal_unknown,
            "min_monthly": job.salary_min_monthly,
            "max_monthly": job.salary_max_monthly,
            "minimum_required": prefs.minimum_salary,
        },
        "location": job.location,
        "work_arrangement": arrangement,
        "work_arrangement_inferred": job.work_arrangement is None and arrangement is not None,
        "requirements": {
            "min_years": req.min_years,
            "education_level": scoring.EDU_NAMES[req.education_level],
            "fresh_graduate_ok": req.fresh_graduate_ok,
        },
        "recommendation": recommendation,
        "suggested_status": status,
    }
