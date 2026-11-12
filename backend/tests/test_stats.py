from datetime import datetime, timezone

from app.db.session import get_sessionmaker
from app.models import Application, ApplicationStatus as S, Job


def _add(db, n: int, status: S, applied: bool) -> None:
    job = Job(source="manual", external_id=str(n), canonical_url=f"https://careers.example.com/jobs/{n}", title=f"Job {n}")
    db.add(job)
    db.flush()
    db.add(Application(job_id=job.id, status=status, applied_at=datetime.now(timezone.utc) if applied else None))


def test_filter_rejects_are_not_counted_as_submissions(auth_client):
    with get_sessionmaker()() as db:
        _add(db, 1, S.REJECTED, applied=False)  # hard-filter reject
        _add(db, 2, S.REJECTED, applied=True)   # employer rejection
        _add(db, 3, S.INTERVIEW, applied=True)
        _add(db, 4, S.APPLIED, applied=True)
        _add(db, 5, S.PENDING_ACTION, applied=False)
        _add(db, 6, S.QUALIFIED, applied=False)
        db.commit()
    o = auth_client.get("/api/dashboard/overview").json()
    assert o["jobs_discovered"] == 6
    assert o["applications_submitted"] == 3
    assert o["rejections"] == 1 and o["filtered_out"] == 1
    assert o["interviews"] == 1 and o["pending"] == 1
    assert o["qualified"] == 5  # qualified + pending + 3 submitted
    assert o["success_rate"] == round(1 / 3 * 100, 1)


def test_cannot_move_submitted_application_back(auth_client):
    job_id = auth_client.post("/api/jobs/import", json={"job_url": "https://careers.example.com/jobs/9", "title": "X"}).json()["job"]["id"]
    url = f"/api/jobs/{job_id}/application/status"
    assert auth_client.put(url, json={"status": "applied", "confirmation": "email"}).status_code == 200
    assert auth_client.put(url, json={"status": "qualified"}).status_code == 422
    assert auth_client.put(url, json={"status": "rejected"}).status_code == 200
