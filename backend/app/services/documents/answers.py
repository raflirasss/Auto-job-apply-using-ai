"""Answers for common application-form questions, sourced only from the profile.

Every answer carries a `source`. Missing facts are returned as MANUAL and must never be
submitted automatically.
"""

from __future__ import annotations

from app.schemas.candidate import CandidateProfileData
from app.services.documents.content import TailoredResume

MANUAL = "REQUIRES YOUR INPUT"


def _yes_no(v: bool | None) -> str | None:
    return None if v is None else ("Yes" if v else "No")


def _idr(v: int | None) -> str | None:
    return f"{v:,}".replace(",", ".") if v else None


def form_answers(profile: CandidateProfileData, resume: TailoredResume) -> list[dict]:
    p, f = profile.personal, profile.application_facts
    latest = profile.experience[0] if profile.experience else None
    all_skills = [s for _, g in resume.skill_groups for s in g]
    rows: list[tuple[str, str, str | None, str]] = [
        ("full_name", "Full name", p.full_name, "profile"),
        ("email", "Email", p.email, "profile"),
        ("phone", "Phone", p.phone, "profile"),
        ("location", "Current location", p.location, "profile"),
        ("website", "Portfolio / website", ", ".join(p.websites) or None, "profile"),
        ("education", "Highest education", (resume.education[0][1] or None) if resume.education else None, "profile"),
        ("institution", "Institution", resume.education[0][0] if resume.education else None, "profile"),
        ("recent_role", "Most recent role", f"{latest.title} at {latest.company}" if latest and latest.title else None, "profile"),
        ("expected_salary", "Expected monthly salary (IDR)", _idr(f.expected_salary_monthly_idr), "application facts"),
        ("availability", "Availability / start date", f.availability_date, "application facts"),
        ("notice_period", "Notice period", f.notice_period, "application facts"),
        ("work_authorization", "Legally allowed to work in Indonesia", _yes_no(f.has_work_authorization_indonesia), "application facts"),
        ("relocate", "Willing to relocate", _yes_no(f.willing_to_relocate), "application facts"),
        ("languages", "Languages", ", ".join(resume.languages) or None, "profile"),
        ("skills", "Key skills", ", ".join(resume.relevant_skills or all_skills[:10]) or None, "profile"),
    ]
    return [
        {"key": key, "question": q, "answer": a if a else MANUAL, "source": src if a else "missing"}
        for key, q, a, src in rows
    ]
