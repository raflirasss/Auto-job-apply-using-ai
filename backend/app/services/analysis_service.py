"""Run the matching engine on stored jobs and persist results."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AgentEvent, Application, ApplicationStatus, Job
from app.schemas.candidate import CandidateProfileData
from app.schemas.settings import Preferences
from app.services import ai_explainer
from app.services.ai_config import resolve_ai_config
from app.services.application_status import POST_SUBMISSION, set_status
from app.services.candidate_service import get_active_profile
from app.services.matching import evaluate
from app.services.settings_store import get_setting

log = logging.getLogger(__name__)


class AnalysisPreconditionError(RuntimeError):
    pass


def _load_inputs(db: Session, settings: Settings) -> tuple[CandidateProfileData, Preferences]:
    profile = get_active_profile(db)
    if profile is None:
        raise AnalysisPreconditionError("No candidate profile. Import your CV first.")
    if not profile.is_confirmed:
        raise AnalysisPreconditionError("Candidate profile is not confirmed. Review and confirm it in Settings first.")
    prefs = get_setting(db, settings, "preferences")
    return CandidateProfileData.model_validate(profile.data), prefs  # type: ignore[return-value]


def _application_for(db: Session, job: Job) -> Application:
    app = db.scalars(select(Application).where(Application.job_id == job.id)).first()
    if app is None:
        app = Application(job_id=job.id, status=ApplicationStatus.DISCOVERED)
        db.add(app)
        db.flush()
    return app


def analyze_job(db: Session, settings: Settings, job: Job, *, profile: CandidateProfileData | None = None,
                prefs: Preferences | None = None, with_ai: bool = False) -> dict:
    if profile is None or prefs is None:
        profile, prefs = _load_inputs(db, settings)
    app = _application_for(db, job)
    duplicate = app.status in POST_SUBMISSION and prefs.avoid_duplicates
    result = evaluate(job, profile, prefs, duplicate_application=duplicate)
    result["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    result["ai_explanation"] = None
    result["ai_error"] = None

    if with_ai:
        cfg = resolve_ai_config(db, settings)
        try:
            result["ai_explanation"] = ai_explainer.explain(job, result, profile, cfg)
            result["ai_model"] = cfg.model
        except ai_explainer.AIExplanationError as exc:
            result["ai_error"] = str(exc)
            log.warning("AI explanation failed for job %s: %s", job.id, exc)

    job.match_score = result["score"]
    job.match_details = result
    if not duplicate:
        set_status(db, app, ApplicationStatus(result["suggested_status"]), f"match {result['score']} ({result['recommendation']})", actor="engine")
    db.add(AgentEvent(category="matching", message=f"Job #{job.id} analysed: score {result['score']}, {result['recommendation']}."))
    db.commit()
    return result


def analyze_pending(db: Session, settings: Settings, *, reanalyze: bool = False, limit: int = 200) -> dict:
    profile, prefs = _load_inputs(db, settings)
    query = select(Job).order_by(Job.discovered_at.desc()).limit(limit)
    if not reanalyze:
        query = query.where(Job.match_details.is_(None))
    jobs = db.scalars(query).all()
    counts: dict[str, int] = {}
    for job in jobs:
        rec = analyze_job(db, settings, job, profile=profile, prefs=prefs)["recommendation"]
        counts[rec] = counts.get(rec, 0) + 1
    return {"analyzed": len(jobs), "by_recommendation": counts}
