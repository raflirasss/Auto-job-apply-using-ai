from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_auth
from app.db.session import get_db
from app.models import CandidateProfile, CandidateProfileVersion, CVFile
from app.schemas.candidate import CandidateProfileData
from app.services import candidate_service
from app.services.categories import category_evidence
from app.services.cv_text import CVExtractionError

router = APIRouter(prefix="/api/candidate", tags=["candidate"], dependencies=[Depends(require_auth)])


def _profile_out(p: CandidateProfile) -> dict:
    return {
        "id": p.id,
        "version": p.version,
        "is_confirmed": p.is_confirmed,
        "source_cv_id": p.source_cv_id,
        "data": CandidateProfileData.model_validate(p.data).model_dump(mode="json"),
        "updated_at": p.updated_at.isoformat(),
    }


def _cv_out(cv: CVFile) -> dict:
    return {
        "id": cv.id,
        "original_filename": cv.original_filename,
        "sha256": cv.sha256,
        "mime_type": cv.mime_type,
        "size_bytes": cv.size_bytes,
        "page_count": cv.page_count,
        "uploaded_at": cv.uploaded_at.isoformat(),
    }


@router.get("/profile")
def get_profile(db: Session = Depends(get_db)) -> dict:
    profile = candidate_service.get_active_profile(db)
    return {"profile": _profile_out(profile) if profile else None}


class ProfileUpdateIn(BaseModel):
    data: CandidateProfileData
    confirm: bool = False


@router.put("/profile")
def put_profile(body: ProfileUpdateIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    try:
        profile = candidate_service.update_profile(db, settings, body.data, body.confirm)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    return {"profile": _profile_out(profile)}


@router.get("/profile/categories")
def get_category_evidence(db: Session = Depends(get_db)) -> dict:
    profile = candidate_service.get_active_profile(db)
    if profile is None:
        return {"categories": []}
    return {"categories": category_evidence(CandidateProfileData.model_validate(profile.data))}


@router.get("/profile/versions")
def list_versions(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(CandidateProfileVersion).order_by(CandidateProfileVersion.version.desc())).all()
    return {
        "versions": [
            {"version": v.version, "change_source": v.change_source, "created_at": v.created_at.isoformat()} for v in rows
        ]
    }


@router.post("/cv")
async def upload_cv(file: UploadFile, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    limit = settings.max_upload_mb * 1024 * 1024
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"File exceeds {settings.max_upload_mb} MB")
    if not content:
        raise HTTPException(422, "Empty file")
    try:
        cv, profile, duplicate, warnings = candidate_service.import_cv(db, settings, file.filename or "cv", content)
    except CVExtractionError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    return {
        "cv_file": _cv_out(cv),
        "profile": _profile_out(profile),
        "duplicate_file": duplicate,
        "extraction_warnings": warnings,
    }


@router.get("/cv")
def list_cvs(db: Session = Depends(get_db)) -> dict:
    return {"files": [_cv_out(cv) for cv in db.scalars(select(CVFile).order_by(CVFile.uploaded_at.desc())).all()]}


@router.get("/cv/{cv_id}/download")
def download_cv(cv_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> FileResponse:
    cv = db.get(CVFile, cv_id)
    if cv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CV not found")
    from pathlib import Path

    path = Path(cv.stored_path).resolve()
    if not path.is_relative_to(settings.cv_storage_dir.resolve()) or not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CV file missing on disk")
    return FileResponse(path, media_type=cv.mime_type, filename=cv.original_filename)
