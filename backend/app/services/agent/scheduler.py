"""APScheduler wiring: daily cron (Asia/Jakarta), manual runs, retries with exponential backoff.

Concurrency: APScheduler runs at most one instance of each job (max_instances=1, coalesce), and
the DB-level guard in runs.start_run rejects a second concurrent run from any trigger.
"""

from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.models import AgentEvent
from app.schemas.settings import SchedulerConfig
from app.services.agent import runs
from app.services.agent.pipeline import run_pipeline
from app.services.notifications import notify
from app.services.settings_store import get_setting

log = logging.getLogger(__name__)
JKT = ZoneInfo("Asia/Jakarta")
DAILY_JOB_ID = "daily_job_hunt"
DISCOVERY_JOB_ID = "periodic_discovery"


class AgentScheduler:
    def __init__(self, apply_fn=None, email_fn=None) -> None:
        self._scheduler: BackgroundScheduler | None = None
        self._lock = threading.Lock()
        self.apply_fn = apply_fn
        self.email_fn = email_fn

    # ---------- lifecycle ----------
    def start(self) -> None:
        with self._lock:
            if self._scheduler is not None:
                return
            with get_sessionmaker()() as db:
                runs.recover_stale(db)
            self._scheduler = BackgroundScheduler(timezone=JKT, job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 3600})
            self._scheduler.start()
            self.apply_config()

    def shutdown(self) -> None:
        with self._lock:
            if self._scheduler is not None:
                self._scheduler.shutdown(wait=False)
                self._scheduler = None

    @property
    def running(self) -> bool:
        return self._scheduler is not None

    def config(self) -> SchedulerConfig:
        with get_sessionmaker()() as db:
            return get_setting(db, get_settings(), "scheduler")  # type: ignore[return-value]

    def apply_config(self) -> None:
        """(Re)register the daily job according to saved settings."""
        if self._scheduler is None:
            return
        cfg = self.config()
        if self._scheduler.get_job(DAILY_JOB_ID):
            self._scheduler.remove_job(DAILY_JOB_ID)
        if self._scheduler.get_job(DISCOVERY_JOB_ID):
            self._scheduler.remove_job(DISCOVERY_JOB_ID)
        if cfg.enabled and not cfg.paused:
            hour, minute = (int(x) for x in cfg.run_time.split(":"))
            self._scheduler.add_job(self._daily, CronTrigger(hour=hour, minute=minute, timezone=JKT), id=DAILY_JOB_ID,
                                    replace_existing=True)
            # Extra discovery-only passes between daily runs (new posts appear all day on Telegram/feeds).
            with get_sessionmaker()() as db:
                hours = get_setting(db, get_settings(), "sources").fetch_interval_hours  # type: ignore[attr-defined]
            self._scheduler.add_job(self._discover, IntervalTrigger(hours=hours, timezone=JKT), id=DISCOVERY_JOB_ID,
                                    replace_existing=True)

    def _discover(self) -> None:
        from app.services.discovery import run_discovery

        with get_sessionmaker()() as db:
            try:
                run_discovery(db, get_settings())
            except Exception:  # noqa: BLE001
                log.exception("Background discovery failed")

    def next_run_time(self) -> str | None:
        job = self._scheduler.get_job(DAILY_JOB_ID) if self._scheduler else None
        return job.next_run_time.isoformat() if job and job.next_run_time else None

    # ---------- execution ----------
    def _daily(self) -> None:
        self.execute("scheduled", runs.daily_key(datetime.now(JKT).date(), 1), attempt=1)

    def trigger_manual(self) -> int:
        """Start a manual run in the background. Returns the run id or raises RunAlreadyActive."""
        with get_sessionmaker()() as db:
            run = runs.start_run(db, "manual", None)
        threading.Thread(target=self._execute_started, args=(run.id,), daemon=True, name=f"agent-run-{run.id}").start()
        return run.id

    def execute(self, trigger: str, key: str | None, attempt: int = 1) -> dict | None:
        try:
            with get_sessionmaker()() as db:
                run = runs.start_run(db, trigger, key, attempt)
        except runs.RunAlreadyActive as exc:
            log.info("Skipped %s run: %s", trigger, exc)
            return None
        return self._execute_started(run.id)

    def _execute_started(self, run_id: int) -> dict | None:
        settings = get_settings()
        with get_sessionmaker()() as db:
            from app.models import AgentRun

            run = db.get(AgentRun, run_id)
            try:
                summary = run_pipeline(db, settings, run, apply_fn=self.apply_fn, email_fn=self.email_fn)
                runs.finish_run(db, run, "succeeded", summary)
                return summary
            except Exception as exc:  # noqa: BLE001 - every failure must be recorded
                db.rollback()
                log.exception("Agent run %s failed", run_id)
                runs.finish_run(db, run, "failed", error=f"{exc.__class__.__name__}: {str(exc)[:500]}")
                self._schedule_retry(db, run)
                return None

    def _schedule_retry(self, db, run) -> None:
        cfg = self.config()
        if run.trigger != "scheduled" or run.attempt >= cfg.max_retries + 1 or self._scheduler is None:
            notify(db, "error", "Agent run failed", run.error or "Unknown error", "/agent")
            db.commit()
            return
        delay = runs.backoff_seconds(run.attempt)
        nxt = run.attempt + 1
        when = datetime.now(timezone.utc) + timedelta(seconds=delay)
        key = runs.daily_key(datetime.now(JKT).date(), nxt)
        self._scheduler.add_job(self.execute, DateTrigger(run_date=when), args=["scheduled", key, nxt],
                                id=f"retry_{key}", replace_existing=True)
        db.add(AgentEvent(run_id=run.id, category="agent", level="warning", message=f"Run failed; retry {nxt} scheduled in {delay}s."))
        db.commit()


agent_scheduler = AgentScheduler()


def today_key() -> str:
    return runs.daily_key(date.today(), 1)
