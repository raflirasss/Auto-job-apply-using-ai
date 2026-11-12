"""Run bookkeeping and scheduler tests."""

from __future__ import annotations

import threading
from datetime import date, timedelta

import pytest

from app.db.session import get_sessionmaker
from app.models import AgentRun, Notification
from app.services.agent import runs
from app.services.agent.scheduler import AgentScheduler

ELIGIBLE = {  # matches the synthetic test CV (backend developer)
    "title": "Backend Developer", "location": "Jakarta Selatan", "work_arrangement": "hybrid",
    "employment_type": "full_time", "salary_min": 9_000_000, "salary_max": 12_000_000, "salary_disclosed": True,
    "description": "Requirements: Python, SQL, Git, Docker. Bachelor of Computer Science. Fresh graduates welcome.",
}


def import_job(client, n: int) -> int:
    body = {**ELIGIBLE, "job_url": f"https://careers.example.com/jobs/{n}"}
    return client.post("/api/jobs/import", json=body).json()["job"]["id"]


def test_single_active_run_and_idempotency(env):
    with get_sessionmaker()() as db:
        run = runs.start_run(db, "scheduled", runs.daily_key(date(2026, 11, 11), 1))
        with pytest.raises(runs.RunAlreadyActive):
            runs.start_run(db, "manual", None)
        runs.finish_run(db, run, "succeeded", {})
        with pytest.raises(runs.RunAlreadyActive):
            runs.start_run(db, "scheduled", runs.daily_key(date(2026, 11, 11), 1))
        assert runs.start_run(db, "manual", None).status == "running"


def test_crash_recovery_marks_stale_runs_failed(env):
    with get_sessionmaker()() as db:
        run = runs.start_run(db, "manual", None)
        run.heartbeat_at = runs.now() - timedelta(hours=2)
        db.commit()
        assert runs.recover_stale(db) == 1
        db.refresh(run)
        assert run.status == "failed" and "Interrupted" in run.error
        assert runs.start_run(db, "manual", None).status == "running"


def test_backoff_is_exponential_and_capped():
    assert [runs.backoff_seconds(a) for a in (1, 2, 3, 4)] == [60, 120, 240, 480]
    assert runs.backoff_seconds(20) == 3600


def test_concurrent_execute_only_one_runs(env, monkeypatch):
    started, release = threading.Event(), threading.Event()

    def slow_pipeline(db, settings, run, **kwargs):
        started.set()
        release.wait(5)
        return {"ok": True}

    monkeypatch.setattr("app.services.agent.scheduler.run_pipeline", slow_pipeline)
    sched = AgentScheduler()
    t = threading.Thread(target=sched.execute, args=("manual", None))
    t.start()
    assert started.wait(5)
    assert sched.execute("manual", None) is None
    release.set()
    t.join(5)
    with get_sessionmaker()() as db:
        assert [r.status for r in db.query(AgentRun).all()] == ["succeeded"]


def test_failed_run_is_recorded_and_notified(env, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr("app.services.agent.scheduler.run_pipeline", boom)
    assert AgentScheduler().execute("manual", None) is None
    with get_sessionmaker()() as db:
        run = db.query(AgentRun).one()
        assert run.status == "failed" and "kaboom" in run.error
        assert db.query(Notification).filter(Notification.level == "error").count() == 1


def test_scheduler_registers_daily_job_and_pause(env):
    from app.core.config import get_settings
    from app.schemas.settings import SchedulerConfig
    from app.services.settings_store import save_setting

    with get_sessionmaker()() as db:
        save_setting(db, get_settings(), "scheduler", SchedulerConfig(enabled=True, run_time="08:00"))
    sched = AgentScheduler()
    sched.start()
    try:
        nxt = sched.next_run_time()
        assert nxt is not None and "T08:00:00+07:00" in nxt
        with get_sessionmaker()() as db:
            save_setting(db, get_settings(), "scheduler", SchedulerConfig(enabled=True, paused=True))
        sched.apply_config()
        assert sched.next_run_time() is None
    finally:
        sched.shutdown()


def test_agent_api(auth_client):
    # Independent of the repository's config/scheduler.json.
    auth_client.put("/api/settings/scheduler", json={"enabled": False, "run_time": "08:00", "timezone": "Asia/Jakarta", "max_retries": 3, "paused": False})
    st = auth_client.get("/api/agent/status").json()
    assert st["enabled"] is False and st["active_run"] is None
    assert auth_client.post("/api/agent/start").json()["enabled"] is True
    assert auth_client.post("/api/agent/pause").json()["paused"] is True
    assert auth_client.post("/api/agent/resume").json()["paused"] is False
    assert auth_client.get("/api/agent/notifications").json()["unread"] == 0
