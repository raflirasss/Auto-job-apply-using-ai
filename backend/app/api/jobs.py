from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_auth
from app.db.session import get_db
from app.models import Application, ApplicationStatus, Job
from app.schemas.jobs import JobImportResult, ManualJobIn
from app.services.analysis_service import AnalysisPreconditionError, analyze_job, analyze_pending
from app.services.application_status import StatusTransitionError, manual_update
from app.services.job_ingestion import ingest_manual_job, job_out, list_jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_auth)])


def _with_application(db: Session, job: Job) -> dict:
    out = job_out(job)
    app = db.scalars(select(Application).where(Application.job_id == job.id)).first()
    out["application"] = None if app is None else {
        "id": app.id,
        "status": app.status.value,
        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
        "submission_confirmation": app.submission_confirmation,
        "notes": app.notes,
        "pending_action": app.pending_action,
        "error_details": app.error_details,
    }
    return out


def _get_job(db: Session, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job


@router.get("")
def get_jobs(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    return {"jobs": [_with_application(db, job) for job in list_jobs(db, limit)]}


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)) -> dict:
    return {"job": _with_application(db, _get_job(db, job_id))}


class AnalyzeIn(BaseModel):
    with_ai: bool = False


@router.post("/{job_id}/analyze")
def analyze_one(job_id: int, body: AnalyzeIn | None = None, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    job = _get_job(db, job_id)
    try:
        analyze_job(db, settings, job, with_ai=bool(body and body.with_ai))
    except AnalysisPreconditionError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"job": _with_application(db, job)}


class AnalyzeAllIn(BaseModel):
    reanalyze: bool = False


@router.post("/analyze")
def analyze_all(body: AnalyzeAllIn | None = None, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    try:
        return analyze_pending(db, settings, reanalyze=bool(body and body.reanalyze))
    except AnalysisPreconditionError as exc:
        raise HTTPException(409, str(exc)) from exc


class StatusIn(BaseModel):
    status: ApplicationStatus
    note: str | None = None
    confirmation: str | None = None


@router.put("/{job_id}/application/status")
def update_status(job_id: int, body: StatusIn, db: Session = Depends(get_db)) -> dict:
    job = _get_job(db, job_id)
    app = db.scalars(select(Application).where(Application.job_id == job.id)).first()
    if app is None:
        raise HTTPException(404, "No application record for this job")
    try:
        manual_update(db, app, body.status, body.note, body.confirmation)
    except StatusTransitionError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    return {"job": _with_application(db, job)}


@router.post("/import", response_model=JobImportResult)
def import_job(body: ManualJobIn, db: Session = Depends(get_db)):
    try:
        job, duplicate = ingest_manual_job(db, body)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    return {"job": job_out(job), "duplicate": duplicate, "note": "Added manually."}

