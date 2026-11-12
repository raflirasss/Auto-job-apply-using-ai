"""Pure content builders: tailored resume structure, cover letter, email, form answers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.candidate import CandidateProfileData
from app.services.matching.vocab import SKILLS, contains, extract_skills

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ID_WORDS = {"dan", "yang", "untuk", "dengan", "kami", "anda", "memiliki", "pengalaman", "mampu", "wajib",
            "minimal", "lowongan", "kerja", "tahun", "bidang", "dalam", "sebagai", "dari"}
EN_WORDS = {"and", "the", "with", "for", "you", "our", "experience", "ability", "must", "required",
            "minimum", "years", "will", "your", "team", "work", "skills"}


def detect_language(text: str | None) -> str:
    words = re.findall(r"[a-z]+", (text or "").lower())
    id_hits = sum(w in ID_WORDS for w in words)
    en_hits = sum(w in EN_WORDS for w in words)
    return "id" if id_hits > en_hits else "en"


def profile_language(profile: CandidateProfileData) -> str:
    """Language the profile itself is written in (documents never translate profile text)."""
    parts = [profile.summary or ""] + [b for e in profile.experience for b in e.responsibilities]
    return detect_language(" ".join(parts))


def format_date(value: str | None) -> str:
    if not value:
        return ""
    if value.strip().lower() in {"present", "now", "current", "sekarang"}:
        return "Present"
    m = re.fullmatch(r"(\d{4})-(\d{2})", value.strip())
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{MONTHS[int(m.group(2)) - 1]} {m.group(1)}"
    return value.strip()


def date_range(start: str | None, end: str | None) -> str:
    a, b = format_date(start), format_date(end)
    return f"{a} – {b}" if a and b and a != b else (a or b)


def _relevance(text: str, job_skills: set[str]) -> int:
    lower = text.lower()
    return sum(1 for s in job_skills for alias in (s.lower(), *SKILLS.get(s, ())) if contains(lower, alias))


def _skill_matches_job(skill: str, job_skills: set[str]) -> bool:
    lower = skill.lower()
    if lower in {s.lower() for s in job_skills}:
        return True
    return bool(extract_skills(skill) & job_skills)


@dataclass
class ResumeExperience:
    company: str
    title: str
    location: str
    dates: str
    bullets: list[str]


@dataclass
class TailoredResume:
    name: str
    contact: list[str]
    summary: str | None
    relevant_skills: list[str]
    skill_groups: list[tuple[str, list[str]]]
    experience: list[ResumeExperience]
    education: list[tuple[str, str, str, str]]  # (institution, degree line, dates, location)
    languages: list[str]
    certifications: list[str]
    projects: list[tuple[str, str]]
    achievements: list[str]
    keywords_used: list[str] = field(default_factory=list)


def build_resume(profile: CandidateProfileData, job_skills: set[str]) -> TailoredResume:
    p = profile.personal
    contact = [x for x in (p.email, p.phone, p.location, *p.websites) if x]

    # Skills: candidate's own skills only. Job-relevant ones first, original order otherwise.
    groups: list[tuple[str, list[str]]] = []
    relevant: list[str] = []
    for g in profile.skills:
        ordered = sorted(g.skills, key=lambda s: not _skill_matches_job(s, job_skills))
        relevant += [s for s in ordered if _skill_matches_job(s, job_skills)]
        groups.append((g.category, ordered))
    groups.sort(key=lambda g: -sum(_skill_matches_job(s, job_skills) for s in g[1]))

    experience = []
    for e in profile.experience:  # keep chronological order of roles; reorder bullets by relevance
        bullets = sorted(e.responsibilities, key=lambda b: -_relevance(b, job_skills))
        experience.append(ResumeExperience(e.company, e.title or "", e.location or "", date_range(e.start_date, e.end_date), bullets))

    education = []
    for ed in profile.education:
        degree = ed.degree or ed.field_of_study or ""
        if ed.gpa is not None:
            degree += f" — GPA {ed.gpa:.2f}" + (f"/{ed.gpa_scale:.2f}" if ed.gpa_scale else "")
        dates = date_range(ed.start_date, ed.end_date) + (" (expected)" if ed.is_expected else "")
        education.append((ed.institution, degree, dates, ed.location or ""))

    profile_text_lower = " ".join([profile.summary or "", *relevant, *(b for e in experience for b in e.bullets)]).lower()
    keywords = sorted(s for s in job_skills if any(contains(profile_text_lower, a) for a in (s.lower(), *SKILLS.get(s, ()))))

    return TailoredResume(
        name=p.full_name or "",
        contact=contact,
        summary=profile.summary,
        relevant_skills=list(dict.fromkeys(relevant))[:12],
        skill_groups=groups,
        experience=experience,
        education=education,
        languages=[f"{lang.name} ({lang.proficiency})" if lang.proficiency else lang.name for lang in profile.languages],
        certifications=[", ".join(x for x in (c.name, c.issuer, format_date(c.date)) if x) for c in profile.certifications],
        projects=[(pr.name, pr.description or "") for pr in profile.projects],
        achievements=list(profile.achievements),
        keywords_used=keywords,
    )
