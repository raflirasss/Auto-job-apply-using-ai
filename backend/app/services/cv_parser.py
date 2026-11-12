"""Deterministic CV parser: positioned text lines -> CandidateProfileData draft.

Only copies what the CV states. Unknown facts stay empty and become questions in
`missing_information`. The result is a draft that the owner reviews and confirms.
"""

from __future__ import annotations

import re
from datetime import date

from app.schemas.candidate import (
    CandidateProfileData,
    Education,
    Language,
    MissingInfo,
    PersonalInfo,
    SkillGroup,
    WorkExperience,
)
from app.services import cv_parse_utils as u
from app.services.cv_text import ExtractedCV, Line


def _split_sections(lines: list[Line]) -> tuple[list[Line], dict[str, list[Line]]]:
    header: list[Line] = []
    sections: dict[str, list[Line]] = {}
    current: str | None = None
    for line in lines:
        key = u.heading_key(line)
        if key:
            current = key
            sections.setdefault(key, [])
        elif current is None:
            header.append(line)
        else:
            sections[current].append(line)
    return header, sections


def _parse_header(header: list[Line]) -> PersonalInfo:
    info = PersonalInfo()
    if not header:
        return info
    joined = " | ".join(line.text for line in header)
    first = header[0].text
    if not u.EMAIL_RE.search(first) and not u.PHONE_RE.search(first) and len(first.split()) <= 8:
        info.full_name = first
    if m := u.EMAIL_RE.search(joined):
        info.email = m.group(0)
    if m := u.PHONE_RE.search(joined):
        info.phone = m.group(0).strip()
    without_email = u.EMAIL_RE.sub(" ", joined)
    info.websites = list(dict.fromkeys(m.group(0).rstrip("/") for m in u.URL_RE.finditer(without_email)))
    return info


def _group_entries(lines: list[Line]) -> list[list[Line]]:
    """An entry starts with a bold, non-indented, left-column line."""
    left = [ln.x0 for ln in lines if not u.is_right_column(ln)]
    margin = min(left, default=0)
    entries: list[list[Line]] = []
    for line in lines:
        starts = line.is_bold and not u.is_right_column(line) and line.x0 <= margin + 5 and not line.is_bullet
        if starts or not entries:
            entries.append([line])
        else:
            entries[-1].append(line)
    return entries


def _entry_meta(entry: list[Line]):
    """Split entry into header lines, body lines, date range and location."""
    start = end = location = None
    present = False
    head: list[Line] = []
    body: list[Line] = []
    margin = entry[0].x0
    for line in entry:
        if u.is_right_column(line):
            rng = u.parse_date_range(line.text)
            if rng:
                start, end, present = rng
            elif location is None:
                location = line.text
        elif body or line.is_bullet or line.x0 > margin + 8:
            body.append(line)
        else:
            head.append(line)
    return head, body, start, end, present, location


def _parse_education(lines: list[Line], today: date) -> list[Education]:
    out: list[Education] = []
    for entry in _group_entries(lines):
        head, body, start, end, _present, location = _entry_meta(entry)
        if not head:
            continue
        edu = Education(institution=head[0].text, location=location, start_date=start, end_date=end)
        for line in head[1:] + body:
            if m := u.GPA_RE.search(line.text):
                edu.gpa = float(m.group("gpa").replace(",", "."))
                if m.group("scale"):
                    edu.gpa_scale = float(m.group("scale").replace(",", "."))
            elif edu.degree is None and (d := u.DEGREE_RE.match(line.text)):
                edu.degree = line.text
                if d.group("field"):
                    edu.field_of_study = d.group("field").strip()
        edu.is_expected = u.date_is_future(end, today)
        out.append(edu)
    return out


def _parse_experience(lines: list[Line]) -> list[WorkExperience]:
    out: list[WorkExperience] = []
    for entry in _group_entries(lines):
        head, body, start, end, present, location = _entry_meta(entry)
        if not head:
            continue
        exp = WorkExperience(
            company=head[0].text,
            title=head[1].text if len(head) > 1 else None,
            location=location,
            start_date=start,
            end_date="present" if present else end,
            responsibilities=u.join_wrapped(body),
        )
        out.append(exp)
    return out


def _parse_skills(lines: list[Line]) -> tuple[list[SkillGroup], list[Language]]:
    groups: list[SkillGroup] = []
    languages: list[Language] = []
    for item in u.join_wrapped(lines):
        category, sep, rest = item.partition(":")
        if not sep:
            category, rest = "General", item
        category = category.strip()
        values = u.split_list(rest)
        if u.LANGUAGE_CATEGORY_RE.match(category):
            for v in values:
                m = u.LANGUAGE_ITEM_RE.match(v)
                if m:
                    languages.append(Language(name=m.group("name").strip(), proficiency=m.group("level")))
        elif values:
            groups.append(SkillGroup(category=category, skills=values))
    return groups, languages


def _parse_languages(lines: list[Line]) -> list[Language]:
    out: list[Language] = []
    for item in u.join_wrapped(lines):
        for v in u.split_list(item):
            if m := u.LANGUAGE_ITEM_RE.match(v):
                out.append(Language(name=m.group("name").strip(), proficiency=m.group("level")))
    return out


def _soft_skills_from(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for term in u.SOFT_SKILL_TERMS:
        if re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", lower):
            found.append(term.replace("detail oriented", "detail-oriented"))
    return found


def build_missing_information(profile: CandidateProfileData) -> list[MissingInfo]:
    """Questions for facts the CV does not state. Never guessed."""
    q: list[MissingInfo] = []
    p = profile.personal
    if not p.full_name:
        q.append(MissingInfo(field="personal.full_name", question="What is your full name as it should appear on applications?"))
    if not p.email:
        q.append(MissingInfo(field="personal.email", question="Which email address should employers use to contact you?"))
    if not p.phone:
        q.append(MissingInfo(field="personal.phone", question="Which phone number should employers use?"))
    if not p.location:
        q.append(MissingInfo(field="personal.location", question="What is your current domicile (city/area)? Application forms commonly require it."))
    facts = profile.application_facts
    if facts.expected_salary_monthly_idr is None:
        q.append(MissingInfo(field="application_facts.expected_salary_monthly_idr", question="What monthly expected salary (IDR) may be entered on application forms?"))
    if not facts.availability_date and not facts.notice_period:
        q.append(MissingInfo(field="application_facts.availability_date", question="When can you start a new job (immediately, or a specific date / notice period)?"))
    if facts.has_work_authorization_indonesia is None:
        q.append(MissingInfo(field="application_facts.has_work_authorization_indonesia", question="Are you legally allowed to work in Indonesia (e.g. Indonesian citizen)?"))
    if facts.willing_to_relocate is None:
        q.append(MissingInfo(field="application_facts.willing_to_relocate", question="Are you willing to relocate within Greater Jakarta if required?", critical=False))
    for i, edu in enumerate(profile.education):
        if edu.is_expected:
            q.append(MissingInfo(field=f"education[{i}].end_date", question=f"Your degree at {edu.institution} ends in the future ({edu.end_date}). Confirm whether you have graduated or the expected graduation date."))
    for i, exp in enumerate(profile.experience):
        if exp.start_date and "-" not in exp.start_date:
            q.append(MissingInfo(field=f"experience[{i}].start_date", question=f"Optional: start/end months for {exp.company} (CV lists years only).", critical=False))
        if not exp.employment_type:
            q.append(MissingInfo(field=f"experience[{i}].employment_type", question=f"Was your role at {exp.company} full-time, part-time, contract, freelance or an internship?", critical=False))
    if not profile.certifications:
        q.append(MissingInfo(field="certifications", question="The CV lists no certifications. Add any you hold, or leave empty.", critical=False))
    if not profile.projects:
        q.append(MissingInfo(field="projects", question="The CV lists no projects (your portfolio site may have some). Add relevant projects, or leave empty.", critical=False))
    return q


def parse_cv(extracted: ExtractedCV, today: date | None = None) -> tuple[CandidateProfileData, list[str]]:
    today = today or date.today()
    warnings = list(extracted.warnings)
    header, sections = _split_sections(extracted.lines)

    profile = CandidateProfileData(personal=_parse_header(header))
    if summary_lines := sections.get("summary"):
        profile.summary = " ".join(u.join_wrapped(summary_lines))
        profile.soft_skills = _soft_skills_from(profile.summary)
    if lines := sections.get("education"):
        profile.education = _parse_education(lines, today)
    if lines := sections.get("experience"):
        profile.experience = _parse_experience(lines)
    if lines := sections.get("skills"):
        profile.skills, profile.languages = _parse_skills(lines)
    if lines := sections.get("languages"):
        profile.languages.extend(_parse_languages(lines))
    if lines := sections.get("achievements"):
        profile.achievements = u.join_wrapped(lines)
    for name in ("certifications", "projects", "organizations"):
        if sections.get(name):
            warnings.append(f"A '{name}' section was found but is not auto-parsed yet; add its entries manually.")

    for required in ("education", "experience", "skills"):
        if required not in sections:
            warnings.append(f"No '{required}' section was detected. Review the profile manually.")

    profile.missing_information = build_missing_information(profile)
    return CandidateProfileData.model_validate(profile.model_dump()), warnings

