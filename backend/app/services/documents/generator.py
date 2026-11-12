"""Generate and version per-application documents; files live under data/documents/."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AgentEvent, Application, ApplicationStatus, Document, Job
from app.schemas.candidate import CandidateProfileData
from app.services.application_status import set_status
from app.services.candidate_service import get_active_profile
from app.services.documents.answers import form_answers
from app.services.documents.content import build_resume, detect_language, profile_language
from app.services.documents.letters import application_email, cover_letter
from app.services.documents.render_docx import render_letter_docx, render_resume_docx
from app.services.documents.render_pdf import render_letter_pdf, render_resume_pdf
from app.services.documents.templates import get_template
from app.services.matching.requirements import extract_requirements

ID_MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


class DocumentPreconditionError(RuntimeError):
    pass


def documents_root(settings: Settings) -> Path:
    return settings.data_dir / "documents"


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:40] or "x"


def _date_text(lang: str) -> str:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    return f"Jakarta, {now.day} {ID_MONTHS[now.month - 1]} {now.year}" if lang == "id" else now.strftime("%d %B %Y")


def generate_for_job(db: Session, settings: Settings, job: Job, *, template_key: str | None = None, lang: str | None = None) -> dict:
    profile_row = get_active_profile(db)
    if profile_row is None or not profile_row.is_confirmed:
        raise DocumentPreconditionError("A confirmed candidate profile is required to generate documents.")
    profile = CandidateProfileData.model_validate(profile_row.data)
    if not profile.personal.full_name:
        raise DocumentPreconditionError("Profile has no full name.")
    app = db.scalars(select(Application).where(Application.job_id == job.id)).first()
    if app is None:
        app = Application(job_id=job.id, status=ApplicationStatus.DISCOVERED)
        db.add(app)
        db.flush()

    template = get_template(template_key)
    # Default: language of the profile text (quoted verbatim), not of the listing.
    lang = lang if lang in {"en", "id"} else profile_language(profile)
    listing_lang = detect_language(job.description)
    req = extract_requirements(job.title, job.description)
    resume = build_resume(profile, req.skills)
    letter = cover_letter(profile, resume, job, lang)
    subject, body = application_email(profile, job, lang)
    answers = form_answers(profile, resume)

    version = (db.scalar(select(func.max(Document.version)).where(Document.application_id == app.id)) or 0) + 1
    folder = documents_root(settings) / f"app_{app.id}" / f"v{version}"
    folder.mkdir(parents=True, exist_ok=False)
    base = f"{_slug(profile.personal.full_name)}_{_slug(job.company or job.title)}"
    contact = resume.contact
    date_text = _date_text(lang)

    files: list[tuple[str, str, Path]] = [
        ("resume", "pdf", folder / f"CV_{base}.pdf"),
        ("resume", "docx", folder / f"CV_{base}.docx"),
        ("cover_letter", "pdf", folder / f"CoverLetter_{base}.pdf"),
        ("cover_letter", "docx", folder / f"CoverLetter_{base}.docx"),
        ("email", "txt", folder / "application_email.txt"),
        ("answers", "json", folder / "form_answers.json"),
    ]
    render_resume_pdf(resume, lang, template, files[0][2])
    render_resume_docx(resume, lang, template, files[1][2])
    render_letter_pdf(resume.name, contact, letter, date_text, template, files[2][2])
    render_letter_docx(resume.name, contact, letter, date_text, template, files[3][2])
    files[4][2].write_text(f"Subject: {subject}\n\n{body}\n", encoding="utf-8")
    files[5][2].write_text(json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8")

    docs = []
    for kind, fmt, path in files:
        d = Document(application_id=app.id, kind=kind, format=fmt, version=version, stored_path=str(path))
        db.add(d)
        docs.append(d)
    if app.status in {ApplicationStatus.QUALIFIED, ApplicationStatus.ANALYZED}:
        set_status(db, app, ApplicationStatus.READY_TO_APPLY, f"documents v{version} generated", actor="engine_docs")
    db.add(AgentEvent(category="documents", message=f"Documents v{version} generated for job #{job.id} ({lang}, {template.key})."))
    db.commit()
    return {
        "application_id": app.id, "version": version, "language": lang, "listing_language": listing_lang,
        "template": template.key,
        "keywords_used": resume.keywords_used,
        "missing_answers": [a["question"] for a in answers if a["source"] == "missing"],
        "documents": [document_out(d) for d in docs],
    }


def document_out(d: Document) -> dict:
    return {"id": d.id, "application_id": d.application_id, "kind": d.kind, "format": d.format,
            "version": d.version, "filename": Path(d.stored_path).name, "created_at": d.created_at.isoformat()}


def list_documents(db: Session, application_id: int | None = None) -> list[Document]:
    q = select(Document).order_by(Document.application_id, Document.version.desc(), Document.id)
    if application_id is not None:
        q = q.where(Document.application_id == application_id)
    return list(db.scalars(q).all())
