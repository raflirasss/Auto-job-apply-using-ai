"""Run every enabled source adapter, ingest results (dedup), and report per source."""

from __future__ import annotations

import logging
import threading

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.crypto import decrypt_secret
from app.models import AgentEvent, StoredCredential
from app.schemas.jobs import ManualJobIn
from app.schemas.settings import Preferences, SourcesConfig
from app.services.job_ingestion import ingest_job
from app.services.settings_store import get_setting
from app.sources import FetchContext, SourceJob, get_adapter
from app.sources.text import parse_salary_label

log = logging.getLogger(__name__)
discovery_lock = threading.Lock()


def secret(db: Session, settings: Settings, name: str) -> str | None:
    row = db.get(StoredCredential, name)
    return decrypt_secret(row.ciphertext, settings) if row else None


def _adapter_configs(db: Session, settings: Settings, cfg: SourcesConfig) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if cfg.rss.enabled:
        out["rss"] = cfg.rss.model_dump()
    if cfg.telegram.enabled:
        tg = cfg.telegram.model_dump()
        tg["api_hash"] = secret(db, settings, "telegram_api_hash")
        tg["session"] = secret(db, settings, "telegram_session")
        out["telegram"] = tg
    if cfg.ats.enabled:
        out["ats"] = cfg.ats.model_dump()
    return out


def to_payload(job: SourceJob) -> ManualJobIn:
    if job.salary_min is not None or job.salary_max is not None:
        disclosed, lo, hi, period, note = True, job.salary_min, job.salary_max or job.salary_min, job.salary_period, None
    else:
        s = parse_salary_label(job.salary_label)
        disclosed, lo, hi, period, note = s.disclosed, s.min_value, s.max_value, s.period, s.note
    notes = list(job.notes) + ([note] if note and job.salary_label else [])
    if job.apply_email:
        notes.append(f"Apply by email: {job.apply_email}")
    return ManualJobIn(
        job_url=job.url, title=job.title[:300] or "Untitled", company=(job.company or None) and job.company[:300],
        location=job.location and job.location[:300], work_arrangement=job.work_arrangement,
        employment_type=job.employment_type, salary_min=lo, salary_max=hi, salary_disclosed=disclosed,
        salary_period=period if period in {"monthly", "annual", "weekly", "daily"} else "monthly",
        description=job.description and job.description[:30000], posted_at=job.posted_at,
        source_note="; ".join(notes)[:500] or None, apply_url=job.apply_url,
    )


def run_discovery(db: Session, settings: Settings, *, only: str | None = None, adapter_override=None) -> dict:
    """Fetch from enabled sources and ingest. Returns {source: {fetched, created, updated, failed, errors, notes}}."""
    if not discovery_lock.acquire(blocking=False):
        return {"_busy": True}
    try:
        cfg: SourcesConfig = get_setting(db, settings, "sources")  # type: ignore[assignment]
        prefs: Preferences = get_setting(db, settings, "preferences")  # type: ignore[assignment]
        ctx = FetchContext(lookback_days=prefs.lookback_days, accepted_locations=prefs.location)
        report: dict[str, dict] = {}
        for name, conf in _adapter_configs(db, settings, cfg).items():
            if only and name != only:
                continue
            adapter = adapter_override(name) if adapter_override else get_adapter(name)
            rep = {"fetched": 0, "created": 0, "updated": 0, "failed": 0, "errors": [], "notes": []}
            try:
                result = adapter.fetch(conf, ctx)
            except Exception as exc:  # adapter bug: report, continue with other sources
                log.exception("Source %s failed", name)
                rep["errors"].append(f"{exc.__class__.__name__}: {str(exc)[:200]}")
                report[name] = rep
                continue
            rep["fetched"], rep["errors"], rep["notes"] = len(result.jobs), result.errors, result.notes
            for sj in result.jobs:
                try:
                    _, dup = ingest_job(db, to_payload(sj), source=sj.source, external_id=sj.external_id,
                                        apply_email=sj.apply_email, commit=False)
                    db.commit()
                    rep["updated" if dup else "created"] += 1
                except (ValidationError, ValueError) as exc:
                    db.rollback()
                    rep["failed"] += 1
                    if len(rep["errors"]) < 10:
                        rep["errors"].append(f"'{sj.title[:60]}': {str(exc)[:150]}")
            report[name] = rep
            db.add(AgentEvent(category="discovery", level="warning" if rep["errors"] else "info",
                              message=f"{adapter.label}: {rep['fetched']} fetched, {rep['created']} new, "
                                      f"{rep['updated']} updated, {rep['failed']} failed."))
            db.commit()
        return report
    finally:
        discovery_lock.release()
