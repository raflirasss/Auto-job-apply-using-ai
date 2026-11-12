"""Decide what to do with each detected field, using only verified candidate facts."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.candidate import CandidateProfileData
from app.services.apply.classify import FormField, classify

REASONS = {
    "sensitive": "sensitive personal data: manual entry only",
    "legal": "legal declaration / consent: requires your confirmation",
    "salary_history": "salary history is never filled automatically",
    "unknown": "unknown question: no verified answer",
}


@dataclass
class FieldDecision:
    field: FormField
    action: str  # fill | upload | select | skip | block
    key: str | None = None
    value: str | None = None  # NEVER persisted or logged
    reason: str = ""


def facts_for(profile: CandidateProfileData) -> dict[str, str | None]:
    p, a = profile.personal, profile.application_facts
    parts = (p.full_name or "").split()

    def yes_no(v: bool | None) -> str | None:
        return None if v is None else ("Yes" if v else "No")

    return {
        "email": p.email,
        "phone": p.phone,
        "full_name": p.full_name,
        "first_name": parts[0] if parts else None,
        "last_name": " ".join(parts[1:]) if len(parts) > 1 else None,
        "location": p.location,
        "website": p.websites[0] if p.websites else None,
        "expected_salary": str(a.expected_salary_monthly_idr) if a.expected_salary_monthly_idr else None,
        "availability": a.availability_date or a.notice_period,
        "work_authorization": yes_no(a.has_work_authorization_indonesia),
        "relocate": yes_no(a.willing_to_relocate),
    }


YES = ("yes", "ya", "bersedia", "true")
NO = ("no", "tidak", "false", "tidak bersedia")


def choose_option(value: str, options: list[str]) -> str | None:
    """Pick the single option matching a fact. Yes/No understood in EN/ID; otherwise exact match only."""
    v = value.strip().lower()
    if v in {"yes", "no"}:
        want = YES if v == "yes" else NO
        hits = [o for o in options if o.strip().lower().rstrip(".") in want]
        return hits[0] if len(hits) == 1 else None
    exact = [o for o in options if o.strip().lower() == v]
    return exact[0] if len(exact) == 1 else None


def _miss(f: FormField, key: str | None, reason: str) -> FieldDecision:
    return FieldDecision(f, "block" if f.required else "skip", key, reason=reason)


def decide(fields: list[FormField], profile: CandidateProfileData, files: dict[str, str | None]) -> list[FieldDecision]:
    """Map every field to an action. `files` maps resume/cover_letter -> local path (or None)."""
    facts = facts_for(profile)
    out: list[FieldDecision] = []
    for f in fields:
        category, key = classify(f)
        if category != "mapped":
            out.append(_miss(f, None, REASONS[category]))
        elif key in {"resume", "cover_letter"}:
            path = files.get(key)
            out.append(FieldDecision(f, "upload", key, path, "generated document") if path
                       else _miss(f, key, f"no {key.replace('_', ' ')} document available"))
        elif not facts.get(key):
            out.append(_miss(f, key, f"profile has no verified value for '{key}'"))
        elif f.options:
            choice = choose_option(facts[key], f.options)
            out.append(FieldDecision(f, "select", key, choice, "verified profile fact") if choice
                       else _miss(f, key, "no option matches the verified answer"))
        elif f.type in {"checkbox", "radio"}:
            out.append(_miss(f, key, "checkbox/radio without options is not auto-answered"))
        else:
            out.append(FieldDecision(f, "fill", key, facts[key], "verified profile fact"))
    return out


def blockers(decisions: list[FieldDecision]) -> list[str]:
    return [f"{d.field.label or d.field.name or d.field.selector}: {d.reason}" for d in decisions if d.action == "block"]


def filled_labels(decisions: list[FieldDecision]) -> list[str]:
    """Labels only (no values) for audit storage."""
    return [d.field.label or d.field.name for d in decisions if d.action in {"fill", "upload", "select"}]
