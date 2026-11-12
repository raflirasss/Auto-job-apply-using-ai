"""Candidate profile import, editing and versioning."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AgentEvent, CandidateProfile, CandidateProfileVersion, CVFile
from app.schemas.candidate import CandidateProfileData
from app.services.cv_parser import build_missing_information, parse_cv
from app.services.cv_text import extract_cv
from app.services.settings_store import atomic_write_json

log = logging.getLogger(__name__)

MIME_BY_KIND = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_active_profile(db: Session) -> CandidateProfile | None:
    return db.scalars(select(CandidateProfile).order_by(CandidateProfile.id).limit(1)).first()


def _snapshot(db: Session, profile: CandidateProfile, source: str) -> None:
    db.add(CandidateProfileVersion(profile=profile, version=profile.version, data=profile.data, change_source=source))


def _mirror_candidate_json(settings: Settings, data: dict) -> None:
    try:
        atomic_write_json(settings.config_dir / "candidate.json", data)
    except OSError as exc:
        log.warning("Could not write candidate.json: %s", exc.__class__.__name__)


def store_cv_file(db: Session, settings: Settings, filename: str, content: bytes) -> tuple[CVFile, bool, list[str], CandidateProfileData]:
    """Store the original CV immutably (content-addressed) and parse it.

    Returns (cv_file, was_duplicate, warnings, parsed_profile).
    """
    kind, extracted = extract_cv(filename, content)
    parsed, warnings = parse_cv(extracted)
    digest = hashlib.sha256(content).hexdigest()

    existing = db.scalars(select(CVFile).where(CVFile.sha256 == digest)).first()
    if existing:
        return existing, True, warnings, parsed

    settings.cv_storage_dir.mkdir(parents=True, exist_ok=True)
    target = settings.cv_storage_dir / f"{digest}.{kind}"
    if not target.exists():  # never overwrite
        with open(target, "xb") as fh:
            fh.write(content)
    safe_name = Path(filename).name[:255] or f"cv.{kind}"
    cv = CVFile(
        original_filename=safe_name,
        stored_path=str(target),
        sha256=digest,
        mime_type=MIME_BY_KIND[kind],
        size_bytes=len(content),
        page_count=extracted.page_count,
        extracted_text=extracted.text,
    )
    db.add(cv)
    db.flush()
    return cv, False, warnings, parsed


def import_cv(db: Session, settings: Settings, filename: str, content: bytes) -> tuple[CVFile, CandidateProfile, bool, list[str]]:
    """Import a CV. Creates the profile or replaces its data with a new *unconfirmed* draft
    (previous versions remain in history)."""
    cv, duplicate, warnings, parsed = store_cv_file(db, settings, filename, content)
    profile = get_active_profile(db)
    data = parsed.model_dump(mode="json")
    if profile is None:
        profile = CandidateProfile(data=data, source_cv_id=cv.id, version=1, is_confirmed=False)
        db.add(profile)
        db.flush()
    else:
        profile.data = data
        profile.source_cv_id = cv.id
        profile.version += 1
        profile.is_confirmed = False
    _snapshot(db, profile, "cv_import")
    db.add(AgentEvent(category="profile", message=f"CV imported (version {profile.version}); awaiting review."))
    db.commit()
    _mirror_candidate_json(settings, data)
    return cv, profile, duplicate, warnings


def update_profile(db: Session, settings: Settings, data: CandidateProfileData, confirm: bool) -> CandidateProfile:
    profile = get_active_profile(db)
    if profile is None:
        raise LookupError("No candidate profile exists yet. Import a CV first.")
    # Recompute questions from the edited facts so answered items disappear.
    data.missing_information = build_missing_information(data)
    profile.data = data.model_dump(mode="json")
    profile.version += 1
    if confirm:
        critical = [m for m in data.missing_information if m.critical]
        if critical:
            raise ValueError(
                "Cannot confirm profile while critical information is missing: "
                + ", ".join(m.field for m in critical)
            )
    profile.is_confirmed = confirm
    _snapshot(db, profile, "confirm" if confirm else "manual_edit")
    db.add(AgentEvent(category="profile", message=f"Profile updated to version {profile.version}" + (" and confirmed." if confirm else ".")))
    db.commit()
    _mirror_candidate_json(settings, profile.data)
    return profile
