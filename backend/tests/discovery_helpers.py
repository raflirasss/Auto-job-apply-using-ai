"""Helpers for discovery / email-apply tests: a fake adapter, a fake SMTP server, setup steps."""

from __future__ import annotations

from app.db.session import get_sessionmaker
from app.models import Job
from app.sources.base import FetchResult, SourceJob
from tests.test_analysis_api import confirmed_profile

TG_JOB = SourceJob(
    source="telegram", external_id="telegram:lokerjkt_test/101", url="https://t.me/lokerjkt_test/101",
    title="Backend Developer", company="PT Contoh", location="Jakarta Selatan", work_arrangement="hybrid",
    employment_type="full_time", salary_label="Gaji: 9 - 12 jt",
    description="Requirements: Python, SQL, Git, Docker. Bachelor of Computer Science. Fresh graduates welcome.",
    apply_email="hr@contoh.co.id", notes=["From Telegram channel @lokerjkt_test."])


class FakeAdapter:
    label = "Fake"

    def __init__(self, jobs):
        self.jobs = jobs

    def fetch(self, config, ctx):
        return FetchResult(jobs=list(self.jobs))


class FakeSMTP:
    sent: list = []

    def __init__(self, cfg, refuse=False):
        self.refuse = refuse

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, user, password):
        assert password == "app-password-123"

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)
        return {msg["To"]: (550, b"no")} if self.refuse else {}


def enable_telegram(client) -> None:
    cfg = client.get("/api/sources").json()["config"]
    cfg["telegram"].update(enabled=True, method="preview", channels=["lokerjkt_test"])
    cfg["ats"]["enabled"] = False
    assert client.put("/api/sources", json=cfg).status_code == 200


def discover(jobs) -> dict:
    from app.core.config import get_settings
    from app.services.discovery import run_discovery

    with get_sessionmaker()() as db:
        return run_discovery(db, get_settings(), adapter_override=lambda name: FakeAdapter(jobs))


def ready_email_job(client, *, smtp: bool = True) -> int:
    confirmed_profile(client)
    enable_telegram(client)
    discover([TG_JOB])
    job_id = client.get("/api/jobs").json()["jobs"][0]["id"]
    rec = client.post(f"/api/jobs/{job_id}/analyze").json()["job"]["match_details"]["recommendation"]
    assert rec == "auto_apply_eligible", rec
    assert client.post(f"/api/jobs/{job_id}/documents").status_code == 200
    if smtp:
        r = client.put("/api/sources/smtp", json={"username": "me@example.com", "password": "app-password-123", "from_name": "Me"})
        assert r.status_code == 200 and r.json()["password_set"] is True
    return job_id


def email_apply(job_id, refuse=False):
    from app.core.config import get_settings
    from app.services.apply.email_service import apply_by_email

    with get_sessionmaker()() as db:
        return apply_by_email(db, get_settings(), db.get(Job, job_id), smtp_factory=lambda cfg: FakeSMTP(cfg, refuse))
