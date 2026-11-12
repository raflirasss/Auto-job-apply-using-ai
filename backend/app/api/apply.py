from __future__ import annotations

import threading
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_auth
from app.db.session import get_db, get_sessionmaker
from app.models import Application, ApplyAttempt, Job
from app.services.apply.policy import allowed_modes, policy_note
from app.services.apply.preflight import ApplyError, latest_files, preflight
from app.services.apply.service import apply_job, browser_lock

router = APIRouter(prefix="/api", tags=["apply"], dependencies=[Depends(require_auth)])
ASSISTED_KEEP_OPEN_SECONDS = 20 * 60


def attempt_out(a: ApplyAttempt) -> dict:
    return {"id": a.id, "application_id": a.application_id, "mode": a.mode, "outcome": a.outcome,
            "stop_reason": a.stop_reason, "detail": a.detail, "fields_filled": a.fields_filled or [],
            "fields_unresolved": a.fields_unresolved or [], "has_screenshot": bool(a.screenshot_path),
            "started_at": a.started_at.isoformat(), "finished_at": a.finished_at.isoformat() if a.finished_at else None}


@router.get("/jobs/{job_id}/apply/status")
def apply_status(job_id: int, db: Session = Depends(get_db)) -> dict:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    app = db.scalars(select(Application).where(Application.job_id == job_id)).first()
    attempts = [] if app is None else db.scalars(
        select(ApplyAttempt).where(ApplyAttempt.application_id == app.id).order_by(ApplyAttempt.id.desc()).limit(10)).all()
    readiness = {}
    for mode in ("assisted", "auto", "email"):
        try:
            preflight(db, job, mode)
            readiness[mode] = None
        except ApplyError as exc:
            readiness[mode] = str(exc)
    return {
        "allowed_modes": allowed_modes(job.application_url, job.apply_email),
        "policy_note": policy_note(job.application_url, job.apply_email),
        "apply_email": job.apply_email,
        "blocked_reason": readiness,
        "has_documents": bool(app and latest_files(db, app.id)["resume"]),
        "browser_busy": browser_lock.locked(),
        "attempts": [attempt_out(a) for a in attempts],
    }


class ApplyIn(BaseModel):
    mode: str = "assisted"


@router.post("/jobs/{job_id}/apply")
def apply(job_id: int, body: ApplyIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if body.mode == "email":
        from app.services.apply.email_service import apply_by_email

        try:
            attempt = apply_by_email(db, settings, job)
        except ApplyError as exc:
            raise HTTPException(409, str(exc)) from exc
        if attempt.outcome != "submitted":
            raise HTTPException(422, attempt.detail or "Email could not be sent.")
        return {"started": True, "mode": "email", "note": attempt.detail}
    try:
        preflight(db, job, body.mode)
    except ApplyError as exc:
        raise HTTPException(409, str(exc)) from exc
    if browser_lock.locked():
        raise HTTPException(409, "Another browser automation is running.")

    def _worker() -> None:
        with get_sessionmaker()() as s:
            j = s.get(Job, job_id)
            try:
                apply_job(s, settings, j, body.mode, keep_open_seconds=ASSISTED_KEEP_OPEN_SECONDS if body.mode == "assisted" else 0)
            except ApplyError:
                pass  # state changed between check and start; nothing was opened

    threading.Thread(target=_worker, daemon=True, name=f"apply-{job_id}").start()
    note = ("A browser window will open on this computer. Log in yourself if asked, review the pre-filled form, "
            "and click submit yourself. Then mark the application as applied." if body.mode == "assisted"
            else "Automatic apply started; results appear in the attempt log.")
    return {"started": True, "mode": body.mode, "note": note}


@router.get("/apply-attempts/{attempt_id}/screenshot")
def screenshot(attempt_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> FileResponse:
    a = db.get(ApplyAttempt, attempt_id)
    if a is None or not a.screenshot_path:
        raise HTTPException(404, "No screenshot")
    path = Path(a.screenshot_path).resolve()
    if not path.is_relative_to((settings.data_dir / "screenshots").resolve()) or not path.exists():
        raise HTTPException(404, "Screenshot missing")
    return FileResponse(path, media_type="image/png")
