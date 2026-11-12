"""Live end-to-end check of Phases 4-6 through the frontend proxy, using the real confirmed profile.

Creates one clearly-marked test job, exercises analysis, documents, apply status and an agent run,
then deletes every row and file it created. Never opens a browser and never contacts JobStreet.
Usage: python -m scripts.smoke_phases [base_url]
"""

from __future__ import annotations

import shutil
import sys
import time

import httpx
from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.models import (AgentEvent, AgentRun, Application, ApplicationStatusHistory, ApplyAttempt, Document, Job,
                        Notification)

MARK = "SMOKE TEST - delete me"
JOB = {
    "job_url": "https://smoke.example.com/jobs/999999998", "title": "Admin Marketplace", "company": MARK,
    "location": "Jakarta Utara", "work_arrangement": "onsite", "employment_type": "full_time",
    "salary_min": 4_500_000, "salary_max": 5_500_000, "salary_disclosed": True,
    "description": "Kualifikasi: wajib menguasai Shopee dan Tokopedia, mampu membuat konten dengan Canva, menguasai Microsoft Excel. Fresh graduate dipersilakan.",
}


def _max_ids() -> dict:
    with get_sessionmaker()() as db:
        ids = {m: db.scalar(select(func.coalesce(func.max(m.id), 0))) for m in (AgentRun, AgentEvent, Notification)}
        ids["job"] = db.scalar(select(func.coalesce(func.max(Job.id), 0)))
        return ids


def _delete_job(db, job_id: int) -> None:
    app_ids = list(db.scalars(select(Application.id).where(Application.job_id == job_id)))
    for app_id in app_ids:
        shutil.rmtree(get_settings().data_dir / "documents" / f"app_{app_id}", ignore_errors=True)
    if app_ids:
        for model in (Document, ApplyAttempt, ApplicationStatusHistory):
            db.execute(delete(model).where(model.application_id.in_(app_ids)))
    db.execute(delete(Application).where(Application.job_id == job_id))
    db.execute(delete(Job).where(Job.id == job_id))


def _cleanup(job_id: int | None, before: dict) -> None:
    """Remove the test job and everything the live run created (incl. jobs discovered from real sources)."""
    with get_sessionmaker()() as db:
        new_jobs = set(db.scalars(select(Job.id).where(Job.id > before["job"])))
        if job_id:
            new_jobs.add(job_id)
        for jid in new_jobs:
            _delete_job(db, jid)
        for model in (AgentEvent, Notification, AgentRun):
            db.execute(delete(model).where(model.id > before[model]))
        db.commit()


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000"
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}{' - ' + detail if detail else ''}")
        if not ok:
            failures.append(name)

    before = _max_ids()
    job_id = None
    try:
        with httpx.Client(base_url=base, timeout=60) as c:
            assert c.post("/api/auth/login", json={"password": get_settings().dashboard_password.get_secret_value()}).status_code == 200
            for page in ("/applications", "/documents", "/agent", "/analysis", "/jobs", "/settings"):
                check(f"page {page} renders", c.get(page).status_code == 200)

            job_id = c.post("/api/jobs/import", json=JOB).json()["job"]["id"]
            d = c.post(f"/api/jobs/{job_id}/analyze", json={}).json()["job"]["match_details"]
            check("phase 3 analysis", d["recommendation"] == "auto_apply_eligible", f"score {d['score']}")

            g = c.post(f"/api/jobs/{job_id}/documents", json={"template": "classic"})
            check("phase 4 documents generated", g.status_code == 200 and len(g.json()["documents"]) == 6,
                  f"lang {g.json().get('language')}, keywords {g.json().get('keywords_used')}")
            pdf = next(x for x in g.json()["documents"] if x["kind"] == "resume" and x["format"] == "pdf")
            check("CV PDF downloadable", c.get(f"/api/documents/{pdf['id']}/download").content[:5] == b"%PDF-")
            check("status ready_to_apply", c.get(f"/api/jobs/{job_id}").json()["job"]["application"]["status"] == "ready_to_apply")

            st = c.get(f"/api/jobs/{job_id}/apply/status").json()
            check("phase 5 modes for an employer form", st["allowed_modes"] == ["assisted", "auto"], str(st["allowed_modes"]))
            check("phase 5 email refused without listing email", c.post(f"/api/jobs/{job_id}/apply", json={"mode": "email"}).status_code == 409)

            # The live agent run must not submit anything real: turn auto-apply off for its duration.
            prefs = c.get("/api/settings/preferences").json()
            c.put("/api/settings/preferences", json={**prefs, "auto_apply": False})
            r = c.post("/api/agent/run")
            check("phase 6 manual run started", r.status_code == 200)
            run = None
            for _ in range(60):
                run = c.get("/api/agent/runs?limit=1").json()["runs"][0]
                if run["status"] != "running":
                    break
                time.sleep(1)
            c.put("/api/settings/preferences", json=prefs)  # restore the owner's setting
            check("phase 6 run succeeded", run and run["status"] == "succeeded", str(run and run.get("summary")))
            check("run submitted nothing", run and run["summary"]["auto_applied"] == 0 and run["summary"]["email_applied"] == 0)
            check("run discovered from sources", run and isinstance(run["summary"]["discovery"], dict), str(run and run["summary"]["discovery"]))
            check("second concurrent run rejected or finished", c.post("/api/agent/run").status_code in (200, 409))
            time.sleep(2)
            check("summary notification", any(n["title"] == "Daily job hunt summary" for n in c.get("/api/agent/notifications").json()["notifications"]))
            check("scheduler status", "next_run_time" in c.get("/api/agent/status").json())
    finally:
        time.sleep(1)
        _cleanup(job_id, before)
        with get_sessionmaker()() as db:
            check("cleanup complete", db.scalar(select(func.count()).select_from(Job).where(Job.company == MARK)) == 0)
    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
