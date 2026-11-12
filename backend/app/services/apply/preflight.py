"""Checks that must pass before any browser is opened."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Application, ApplicationStatus, ApplyAttempt, Document, Job
from app.schemas.candidate import CandidateProfileData
from app.services.apply.policy import allowed_modes
from app.services.candidate_service import get_active_profile

SUBMITTED = {ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW, ApplicationStatus.ASSESSMENT, ApplicationStatus.ACCEPTED}


class ApplyError(RuntimeError):
    pass


def latest_files(db: Session, app_id: int) -> dict[str, str | None]:
    out: dict[str, str | None] = {"resume": None, "cover_letter": None}
    version = db.scalar(select(func.max(Document.version)).where(Document.application_id == app_id))
    if version is None:
        return out
    q = select(Document).where(Document.application_id == app_id, Document.version == version, Document.format == "pdf")
    for d in db.scalars(q):
        if d.kind in out and Path(d.stored_path).exists():
            out[d.kind] = d.stored_path
    return out


def preflight(db: Session, job: Job, mode: str) -> tuple[Application, CandidateProfileData]:
    profile_row = get_active_profile(db)
    if profile_row is None or not profile_row.is_confirmed:
        raise ApplyError("A confirmed candidate profile is required.")
    modes = allowed_modes(job.application_url, job.apply_email)
    if mode not in modes:
        raise ApplyError(f"Mode '{mode}' is not permitted for this site. Allowed: {', '.join(modes) or 'none'}.")
    app = db.scalars(select(Application).where(Application.job_id == job.id)).first()
    if app is None:
        raise ApplyError("No application record for this job.")
    if app.status in SUBMITTED:
        raise ApplyError("Already applied to this job (duplicate prevention).")
    details = job.match_details or {}
    if not details.get("passed_hard_filters", False):
        raise ApplyError("The job must be analysed and pass all hard filters before applying.")
    if mode in {"auto", "email"} and details.get("recommendation") != "auto_apply_eligible":
        raise ApplyError(f"'{mode}' mode requires an 'auto_apply_eligible' match.")
    if not latest_files(db, app.id)["resume"]:
        raise ApplyError("Generate documents first (a tailored CV is required).")
    running = db.scalar(select(func.count()).select_from(ApplyAttempt).where(
        ApplyAttempt.application_id == app.id, ApplyAttempt.outcome == "running"))
    if running:
        raise ApplyError("An apply attempt for this job is already running.")
    return app, CandidateProfileData.model_validate(profile_row.data)
