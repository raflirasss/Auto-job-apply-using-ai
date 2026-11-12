"""Live smoke test against running servers (frontend proxy -> backend).

Usage: python -m scripts.smoke_test [base_url]   (default http://127.0.0.1:3000)
Reads DASHBOARD_PASSWORD from settings; never prints secrets or personal data.
"""

from __future__ import annotations

import sys

import httpx

from app.core.config import get_settings


def _delete_job(job_id: int) -> None:
    """Remove the smoke-test job and its dependent rows so no fake data remains."""
    from sqlalchemy import delete

    from app.db.session import get_sessionmaker
    from app.models import AgentEvent, Application, ApplicationStatusHistory, Job

    with get_sessionmaker()() as db:
        app_ids = [a.id for a in db.query(Application).filter(Application.job_id == job_id)]
        if app_ids:
            db.execute(delete(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id.in_(app_ids)))
        db.execute(delete(Application).where(Application.job_id == job_id))
        db.execute(delete(AgentEvent).where(AgentEvent.message.like(f"Job #{job_id} analysed%")))
        db.execute(delete(Job).where(Job.id == job_id))
        db.execute(delete(AgentEvent).where(AgentEvent.message.like("%SMOKE TEST - delete me%")))
        db.commit()


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000"
    password = get_settings().dashboard_password.get_secret_value()
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}{' - ' + detail if detail else ''}")
        if not ok:
            failures.append(name)

    with httpx.Client(base_url=base, follow_redirects=False, timeout=15) as c:
        r = c.get("/")
        check("unauthenticated page redirects to /login", r.status_code in (302, 307) and "/login" in r.headers.get("location", ""))
        check("unauthenticated API rejected", c.get("/api/candidate/profile").status_code == 401)
        check("wrong password rejected", c.post("/api/auth/login", json={"password": "definitely-wrong"}).status_code == 401)

        r = c.post("/api/auth/login", json={"password": password})
        check("login succeeds", r.status_code == 200)
        cookie = r.headers.get("set-cookie", "").lower()
        check("session cookie httpOnly + SameSite=strict", "httponly" in cookie and "samesite=strict" in cookie)

        check("login page loads", c.get("/login").status_code in (200, 307))
        for page in ("/", "/settings", "/documents", "/agent", "/jobs"):
            check(f"page {page} renders", c.get(page).status_code == 200)

        profile = c.get("/api/candidate/profile").json()["profile"]
        check("profile exists", profile is not None)
        if profile:
            d = profile["data"]
            check("profile has education", len(d["education"]) >= 1, f"{len(d['education'])} entries")
            check("profile has experience", len(d["experience"]) >= 1, f"{len(d['experience'])} entries")
            check("profile has skill groups", len(d["skills"]) >= 1, f"{len(d['skills'])} groups")
            crit = [m["field"] for m in d["missing_information"] if m["critical"]]
            print(f"       critical open questions: {crit}")

        cats = c.get("/api/candidate/profile/categories").json()["categories"]
        print("       supported categories:", [x["category"] for x in cats if x["supported"]])
        ov = c.get("/api/dashboard/overview").json()
        check("overview returns counts", isinstance(ov["jobs_discovered"], int) and ov["applications_submitted"] >= 0,
              f"{ov['jobs_discovered']} jobs, {ov['applications_submitted']} submitted")
        check("preferences load", c.get("/api/settings/preferences").json()["minimum_salary"] == 3500000)
        cvs = c.get("/api/candidate/cv").json()["files"]
        if cvs:
            dl = c.get(f"/api/candidate/cv/{cvs[0]['id']}/download")
            check("original CV downloadable", dl.status_code == 200 and dl.content[:5] == b"%PDF-")
        # Phase 2: manual import + dedup through the proxy, then remove the test row.
        test_url = "https://smoke.example.com/jobs/999999999?utm_source=smoke"
        body = {"job_url": test_url, "title": "SMOKE TEST - delete me", "salary_disclosed": False}
        r1 = c.post("/api/jobs/import", json=body)
        r2 = c.post("/api/jobs/import", json={**body, "job_url": "https://smoke.example.com/jobs/999999999"})
        check("job import works", r1.status_code == 200 and r1.json()["duplicate"] is False)
        check("duplicate detected via canonical URL", r2.status_code == 200 and r2.json()["duplicate"] is True)
        js = c.post("/api/jobs/import", json={**body, "job_url": "https://id.jobstreet.com/id/job/1"})
        check("JobStreet URLs rejected", js.status_code == 422)
        check("sources endpoint", "config" in c.get("/api/sources").json())
        if r1.status_code == 200:
            jid = r1.json()["job"]["id"]
            # Phase 3: analysis (requires a confirmed profile) + manual status guard
            a = c.post(f"/api/jobs/{jid}/analyze", json={})
            if a.status_code == 409:
                print(f"       analysis skipped: {a.json()['detail']}")
            else:
                details = a.json()["job"]["match_details"]
                check("analysis returns score", a.status_code == 200 and details["score"] is not None,
                      f"score {details['score']}, {details['recommendation']}")
                check("analysis page renders", c.get(f"/analysis?job={jid}").status_code == 200)
            g = c.put(f"/api/jobs/{jid}/application/status", json={"status": "applied"})
            check("applied without confirmation rejected", g.status_code == 422)
            _delete_job(jid)
        check("smoke job removed", all("smoke.example.com" not in j["canonical_url"] for j in c.get("/api/jobs").json()["jobs"]))

        check("logout", c.post("/api/auth/logout").status_code == 200)

    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
