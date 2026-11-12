from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_auth
from app.db.session import get_db
from app.models import Document, Job
from app.services.documents.generator import (
    DocumentPreconditionError,
    document_out,
    documents_root,
    generate_for_job,
    list_documents,
)
from app.services.documents.templates import TEMPLATES

router = APIRouter(prefix="/api", tags=["documents"], dependencies=[Depends(require_auth)])

MEDIA = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain; charset=utf-8",
    "json": "application/json",
}


class GenerateIn(BaseModel):
    template: str | None = Field(default=None, max_length=30)
    language: str | None = Field(default=None, pattern="^(en|id)$")


@router.get("/documents/templates")
def templates() -> dict:
    return {"templates": [{"key": t.key, "name": t.name} for t in TEMPLATES.values()]}


@router.post("/jobs/{job_id}/documents")
def generate(job_id: int, body: GenerateIn | None = None, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    body = body or GenerateIn()
    if body.template and body.template not in TEMPLATES:
        raise HTTPException(422, f"Unknown template '{body.template}'")
    try:
        return generate_for_job(db, settings, job, template_key=body.template, lang=body.language)
    except DocumentPreconditionError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/documents")
def documents(application_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    rows = list_documents(db, application_id)
    jobs: dict[int, dict] = {}
    for d in rows:
        if d.application_id is not None and d.application_id not in jobs and d.application is not None:
            j = d.application.job
            jobs[d.application_id] = {"job_id": j.id, "title": j.title, "company": j.company}
    return {"documents": [{**document_out(d), "job": jobs.get(d.application_id)} for d in rows]}


@router.get("/documents/{doc_id}/download")
def download(doc_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> FileResponse:
    d = db.get(Document, doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    path = Path(d.stored_path).resolve()
    if not path.is_relative_to(documents_root(settings).resolve()) or not path.exists():
        raise HTTPException(404, "Document file missing on disk")
    return FileResponse(path, media_type=MEDIA.get(d.format, "application/octet-stream"), filename=path.name)
