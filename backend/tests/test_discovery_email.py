"""Discovery into the database, sources API, and email applications (mocked SMTP)."""

from __future__ import annotations

from email import message_from_bytes

from app.db.session import get_sessionmaker
from app.models import Application, ApplicationStatus, ApplyAttempt
from app.sources.base import SourceJob
from tests.discovery_helpers import TG_JOB, FakeSMTP, discover, email_apply, enable_telegram, ready_email_job


def test_sources_api_validation(auth_client):
    cfg = auth_client.get("/api/sources").json()["config"]
    cfg["telegram"]["channels"] = ["not a channel!"]
    assert auth_client.put("/api/sources", json=cfg).status_code == 422
    cfg["telegram"]["channels"] = ["https://t.me/s/lokerjkt_test", "@lokerjkt_test"]
    r = auth_client.put("/api/sources", json=cfg).json()
    assert r["config"]["telegram"]["channels"] == ["lokerjkt_test"]
    assert r["telegram_connected"] is False and r["smtp"]["password_set"] is False


def test_discovery_ingests_dedups_and_keeps_apply_email(auth_client):
    enable_telegram(auth_client)
    rep = discover([TG_JOB])["telegram"]
    assert (rep["fetched"], rep["created"], rep["failed"]) == (1, 1, 0), rep
    assert discover([TG_JOB])["telegram"]["updated"] == 1  # second run: dedup
    job = auth_client.get("/api/jobs").json()["jobs"][0]
    assert job["apply_email"] == "hr@contoh.co.id" and job["source"] == "telegram"
    assert (job["salary_min_monthly"], job["salary_max_monthly"]) == (9_000_000, 12_000_000)


def test_bad_items_are_counted_not_fatal(auth_client):
    enable_telegram(auth_client)
    bad = SourceJob(source="telegram", external_id="x", url="https://id.jobstreet.com/id/job/1", title="Bad")
    rep = discover([bad, TG_JOB])["telegram"]
    assert rep["created"] == 1 and rep["failed"] == 1 and rep["errors"]


def test_email_apply_sends_documents_and_marks_applied(auth_client):
    FakeSMTP.sent = []
    job_id = ready_email_job(auth_client)
    st = auth_client.get(f"/api/jobs/{job_id}/apply/status").json()
    assert st["allowed_modes"] == ["email"] and st["blocked_reason"]["email"] is None
    assert email_apply(job_id).outcome == "submitted"
    msg = message_from_bytes(FakeSMTP.sent[0].as_bytes())
    assert msg["To"] == "hr@contoh.co.id" and "Backend Developer" in msg["Subject"]
    names = [p.get_filename() for p in msg.walk() if p.get_filename()]
    assert any(n.startswith("CV_") for n in names) and any(n.startswith("CoverLetter_") for n in names)
    with get_sessionmaker()() as db:
        app = db.query(Application).one()
        assert app.status == ApplicationStatus.APPLIED and app.submission_confirmation.startswith("[email]")
    assert auth_client.post(f"/api/jobs/{job_id}/apply", json={"mode": "email"}).status_code == 409  # never twice


def test_refused_email_is_not_success(auth_client):
    job_id = ready_email_job(auth_client)
    assert email_apply(job_id, refuse=True).outcome == "failed"
    with get_sessionmaker()() as db:
        app = db.query(Application).one()
        assert app.status == ApplicationStatus.PENDING_ACTION and app.applied_at is None
        assert db.query(ApplyAttempt).one().stop_reason == "email_error"


def test_email_requires_smtp(auth_client):
    job_id = ready_email_job(auth_client, smtp=False)
    r = auth_client.post(f"/api/jobs/{job_id}/apply", json={"mode": "email"})
    assert r.status_code == 409 and "SMTP" in r.json()["detail"]
