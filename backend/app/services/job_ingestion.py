"""Ingestion of listings from any source (adapters or manual entry): validation, normalisation, dedup."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import AgentEvent, Application, ApplicationStatus, Job
from app.services.job_normalize import canonicalize_url, normalize_location, normalize_salary

__all__ = ["canonicalize_url", "ingest_job", "ingest_manual_job", "job_out", "list_jobs", "normalize_salary"]


def ingest_job(db: Session, payload, *, source: str = "manual", external_id: str | None = None,
               apply_email: str | None = None, commit: bool = True) -> tuple[Job, bool]:
    """Create or update one listing. Duplicate when the canonical URL or (source, external_id) matches."""
    url = canonicalize_url(payload.job_url)
    external_id = (external_id or payload.external_id or url)[:200]
    existing = db.scalars(select(Job).where(or_(
        Job.canonical_url == url, (Job.source == source) & (Job.external_id == external_id)))).first()
    salary_min = normalize_salary(payload.salary_min, payload.salary_period) if payload.salary_disclosed else None
    salary_max = normalize_salary(payload.salary_max, payload.salary_period) if payload.salary_disclosed else None
    if salary_min is not None and salary_max is not None and salary_max < salary_min:
        raise ValueError("salary_max must be >= salary_min")
    apply_url = getattr(payload, "apply_url", None)
    values = dict(
        title=payload.title.strip(), company=payload.company.strip() if payload.company else None,
        location=normalize_location(payload.location), work_arrangement=payload.work_arrangement,
        employment_type=payload.employment_type, salary_min_monthly=salary_min, salary_max_monthly=salary_max,
        salary_currency="IDR" if payload.salary_disclosed else None, salary_disclosed=payload.salary_disclosed,
        description=payload.description, application_url=canonicalize_url(apply_url) if apply_url else url,
        apply_email=apply_email, posted_at=payload.posted_at,
        raw={"ingestion": source, "source_note": payload.source_note},
    )
    if existing:
        _merge(existing, values, overwrite=source == "manual")
        if commit:
            db.commit()
        return existing, True
    job = Job(source=source, external_id=external_id, canonical_url=url, **values)
    db.add(job)
    db.flush()
    db.add(Application(job_id=job.id, status=ApplicationStatus.DISCOVERED))
    if source == "manual":
        db.add(AgentEvent(category="jobs", message=f"Job added manually: {job.title}"))
    if commit:
        db.commit()
    return job, False


def ingest_manual_job(db: Session, payload, ingestion: str = "manual") -> tuple[Job, bool]:
    return ingest_job(db, payload, source=ingestion)


_NULL_OK = {"salary_min_monthly", "salary_max_monthly", "salary_currency"}


def _merge(existing: Job, values: dict, *, overwrite: bool) -> None:
    """Manual edits overwrite everything. Source refreshes never replace richer data with poorer data."""
    changed = False
    for key, value in values.items():
        current = getattr(existing, key)
        if not overwrite:
            if key == "description" and current and (not value or len(value) < len(current)):
                continue
            if value is None and key not in _NULL_OK:
                continue
            if key.startswith("salary") and not values["salary_disclosed"] and existing.salary_disclosed:
                continue
            if key == "raw" and current:
                continue
        if current != value:
            setattr(existing, key, value)
            changed = True
    if changed:  # listing data changed: the previous match result is stale
        existing.match_score = None
        existing.match_details = None


def job_out(job: Job) -> dict:
    return {
        "id": job.id, "source": job.source, "external_id": job.external_id, "canonical_url": job.canonical_url,
        "title": job.title, "company": job.company, "location": job.location, "work_arrangement": job.work_arrangement,
        "employment_type": job.employment_type, "salary_min_monthly": job.salary_min_monthly,
        "salary_max_monthly": job.salary_max_monthly, "salary_currency": job.salary_currency,
        "salary_disclosed": job.salary_disclosed, "description": job.description,
        "application_url": job.application_url, "apply_email": job.apply_email,
        "source_note": (job.raw or {}).get("source_note"),
        "posted_at": job.posted_at.isoformat() if job.posted_at else None, "discovered_at": job.discovered_at.isoformat(),
        "is_available": job.is_available, "match_score": job.match_score, "match_details": job.match_details,
    }


def list_jobs(db: Session, limit: int = 100) -> list[Job]:
    return db.scalars(select(Job).order_by(Job.discovered_at.desc(), Job.id.desc()).limit(limit)).all()
