"""Hard filters (reject) and concerns (warn / block auto-apply). Deterministic only."""

from __future__ import annotations

from app.schemas.settings import Preferences
from app.services.matching.candidate import CandidateFacts
from app.services.matching.location import location_matches
from app.services.matching.requirements import JobRequirements


def salary_unknown(job) -> bool:
    return not job.salary_disclosed or (job.salary_min_monthly is None and job.salary_max_monthly is None)


def hard_filters(
    job, req: JobRequirements, cand: CandidateFacts, prefs: Preferences, *,
    arrangement: str | None, title_cats: set[str], title_score: float, edu_note: str, title_note: str,
    duplicate_application: bool,
) -> list[dict]:
    out: list[dict] = []

    def fail(code: str, reason: str) -> None:
        out.append({"code": code, "reason": reason})

    if not salary_unknown(job):
        top = job.salary_max_monthly if job.salary_max_monthly is not None else job.salary_min_monthly
        if top < prefs.minimum_salary:
            fail("salary_below_minimum", f"Maximum monthly salary IDR {top:,.0f} is below the IDR {prefs.minimum_salary:,} minimum.")
    if location_matches(job.location, prefs.location) is False:
        fail("unsupported_location", f"Location '{job.location}' is outside the accepted locations.")
    if arrangement == "remote" and not prefs.allow_remote:
        fail("fully_remote", "Fully remote position; remote jobs are disabled in preferences.")
    elif arrangement and arrangement not in prefs.work_arrangement:
        fail("work_arrangement", f"Work arrangement '{arrangement}' is not in preferences.")
    if job.employment_type and job.employment_type not in prefs.employment_types:
        fail("employment_type", f"Employment type '{job.employment_type}' is not in preferences.")
    cand_lower = {x.lower() for x in cand.skills}
    missing_mandatory = sorted(s for s in req.mandatory_skills if s.lower() not in cand_lower)
    if missing_mandatory:
        fail("missing_mandatory_skills", f"Mandatory skills not in profile: {', '.join(missing_mandatory)}.")
    if req.education_mandatory and cand.education_level < req.education_level:
        fail("education_requirement", edu_note)
    years = cand.total_experience_months / 12
    if req.min_years and cand.experience_dates_known and years < req.min_years * 0.5:
        fail("insufficient_experience", f"Requires {req.min_years}+ years of experience; profile shows {years:.1f}.")
    if title_cats and not (title_cats & cand.supported_categories) and title_score <= 10:
        fail("incompatible_position", title_note)
    if duplicate_application:
        fail("duplicate_application", "An application for this job was already submitted.")
    return out


def concerns(job, req: JobRequirements, cand: CandidateFacts, arrangement: str | None) -> list[str]:
    out: list[str] = []
    years = cand.total_experience_months / 12
    if salary_unknown(job):
        out.append("Salary undisclosed: the IDR minimum cannot be verified.")
    if job.location is None:
        out.append("Location not provided.")
    if arrangement is None:
        out.append("Work arrangement not stated.")
    if not (job.description or "").strip():
        out.append("No job description: skill and requirement analysis is limited.")
    elif not req.skills:
        out.append("No recognisable skills found in the description.")
    if req.min_years and not cand.experience_dates_known:
        out.append("Some experience dates are missing; years of experience could not be fully verified.")
    if req.min_years and req.min_years * 0.5 <= years < req.min_years:
        out.append(f"Experience (about {years:.1f} years) is below the stated {req.min_years}+ years.")
    if req.education_level and cand.education_level >= req.education_level and not cand.education_completed:
        out.append("Degree is marked as not yet completed.")
    return out
