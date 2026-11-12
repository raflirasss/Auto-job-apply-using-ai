"""Daily pipeline: discover (RSS / Telegram / company boards) -> match -> documents -> apply -> notify."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AgentEvent, AgentRun, Application, ApplicationStatus, ApplyAttempt, Document, Job
from app.schemas.settings import Preferences
from app.services.agent.runs import heartbeat
from app.services.analysis_service import AnalysisPreconditionError, analyze_pending
from app.services.apply.policy import allowed_modes
from app.services.apply.preflight import ApplyError
from app.services.documents.generator import DocumentPreconditionError, generate_for_job
from app.services.notifications import notify
from app.services.discovery import run_discovery
from app.services.settings_store import get_setting

log = logging.getLogger(__name__)
JKT = ZoneInfo("Asia/Jakarta")


def _event(db: Session, run: AgentRun, message: str, level: str = "info") -> None:
    db.add(AgentEvent(run_id=run.id, category="agent", level=level, message=message))
    db.commit()


def submitted_today(db: Session) -> int:
    """Applications confirmed submitted today (Asia/Jakarta), by any mode."""
    start = datetime.now(JKT).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    return db.scalar(select(func.count()).select_from(Application).where(Application.applied_at >= start)) or 0


def _needs_documents(db: Session, app: Application) -> bool:
    return not db.scalar(select(func.count()).select_from(Document).where(Document.application_id == app.id))


def run_pipeline(db: Session, settings: Settings, run: AgentRun, *, apply_fn=None, email_fn=None,
                 discovery_fn=run_discovery) -> dict:
    prefs: Preferences = get_setting(db, settings, "preferences")  # type: ignore[assignment]
    summary: dict = {"discovery": {}, "discovered_new": 0, "analyzed": 0, "by_recommendation": {},
                     "documents_generated": 0, "auto_applied": 0, "email_applied": 0, "awaiting_manual_apply": 0,
                     "apply_stopped": 0, "notes": []}

    # 1-4. Discovery from enabled sources (dedup happens during ingestion).
    report = discovery_fn(db, settings) if discovery_fn else {}
    if report.get("_busy"):
        summary["notes"].append("Discovery skipped: another discovery is running.")
    else:
        summary["discovery"] = {k: {x: v[x] for x in ("fetched", "created", "updated", "failed")} for k, v in report.items()}
        summary["discovered_new"] = sum(v["created"] for v in report.values())
        for name, rep in report.items():
            summary["notes"] += [f"{name}: {e}" for e in rep["errors"][:3]]
        if not report:
            summary["notes"].append("No source is enabled. Configure sources in Settings → Sources.")
    _event(db, run, f"Discovery: {summary['discovered_new']} new listing(s).")
    heartbeat(db, run)

    # 5-6. Hard filters + matching on everything not analysed yet.
    try:
        r = analyze_pending(db, settings)
        summary["analyzed"], summary["by_recommendation"] = r["analyzed"], r["by_recommendation"]
    except AnalysisPreconditionError as exc:
        summary["notes"].append(str(exc))
        _event(db, run, f"Matching skipped: {exc}", "warning")
        return summary
    heartbeat(db, run)

    # 7. Documents for auto-apply-eligible jobs (review-queue jobs get documents on demand).
    eligible = db.scalars(select(Application).join(Job).where(Application.status == ApplicationStatus.QUALIFIED)).all()
    for app in eligible:
        if _needs_documents(db, app):
            try:
                generate_for_job(db, settings, app.job)
                summary["documents_generated"] += 1
            except DocumentPreconditionError as exc:
                summary["notes"].append(f"Documents for job #{app.job_id}: {exc}")
    heartbeat(db, run)

    # 8. Permitted application workflows, within the daily limit.
    ready = db.scalars(select(Application).join(Job).where(Application.status == ApplicationStatus.READY_TO_APPLY)
                       .order_by(Job.match_score.desc())).all()
    budget = max(0, prefs.daily_application_limit - submitted_today(db))
    for app in ready:
        job = app.job
        recent_attempt = db.scalar(select(func.count()).select_from(ApplyAttempt).where(
            ApplyAttempt.application_id == app.id, ApplyAttempt.started_at >= datetime.now(timezone.utc) - timedelta(hours=20)))
        modes = allowed_modes(job.application_url, job.apply_email)
        eligible_rec = (job.match_details or {}).get("recommendation") == "auto_apply_eligible"
        # Email first (most reliable), then the employer's own form.
        mode = next((m for m in ("email", "auto") if m in modes), None) if prefs.auto_apply and eligible_rec else None
        fn = {"email": email_fn, "auto": apply_fn}.get(mode or "")
        if mode is None:
            summary["awaiting_manual_apply"] += 1
            continue
        if budget <= 0:
            summary["notes"].append("Daily application limit reached.")
            break
        if recent_attempt or fn is None:
            continue
        try:
            attempt = fn(db, settings, job) if mode == "email" else fn(db, settings, job, "auto")
        except ApplyError as exc:
            summary["notes"].append(f"Job #{job.id}: {exc}")
            continue
        if attempt.outcome == "submitted":
            summary["email_applied" if mode == "email" else "auto_applied"] += 1
            budget -= 1
        else:
            summary["apply_stopped"] += 1
        heartbeat(db, run)

    # 9-11. Results saved above; dashboard reads live tables; notify.
    recs = summary["by_recommendation"]
    body = (f"New listings: {summary['discovered_new']}. Analysed {summary['analyzed']}: "
            f"{recs.get('auto_apply_eligible', 0)} eligible, {recs.get('review', 0)} to review. "
            f"Documents: {summary['documents_generated']}. Applied by email: {summary['email_applied']}, "
            f"by form: {summary['auto_applied']}. Waiting for you: {summary['awaiting_manual_apply']}.")
    notify(db, "info", "Daily job hunt summary", body, "/applications")
    db.commit()
    return summary
