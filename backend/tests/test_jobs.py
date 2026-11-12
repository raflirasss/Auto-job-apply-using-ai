import pytest

from app.services.job_ingestion import canonicalize_url, normalize_salary


def test_url_canonicalization():
    url = canonicalize_url("http://Careers.Example.com//jobs/123/?utm_source=x&ref=abc&lang=id")
    assert url == "https://careers.example.com/jobs/123?lang=id"


@pytest.mark.parametrize("bad", ["ftp://x.com/a", "not a url", "https://id.jobstreet.com/id/job/1"])
def test_url_rejected(bad):
    with pytest.raises(ValueError):
        canonicalize_url(bad)


def test_salary_normalization():
    assert normalize_salary(120_000_000, "annual") == 10_000_000
    assert normalize_salary(1_000_000, "weekly") == round(1_000_000 * 52 / 12, 2)
    assert normalize_salary(None, "monthly") is None


BODY = {
    "job_url": "https://careers.example.com/jobs/marketing-123?utm_campaign=x",
    "title": "Digital Marketing Specialist", "company": "Example Co", "location": "South Jakarta",
    "work_arrangement": "onsite", "employment_type": "full_time", "salary_min": 60_000_000, "salary_max": 84_000_000,
    "salary_period": "annual", "salary_disclosed": True, "description": "Manage social media campaigns.",
}


def test_manual_import_dedup_and_application_record(auth_client):
    r = auth_client.post("/api/jobs/import", json=BODY)
    assert r.status_code == 200, r.text
    assert r.json()["duplicate"] is False and r.json()["job"]["salary_min_monthly"] == 5_000_000
    assert auth_client.post("/api/jobs/import", json=BODY).json()["duplicate"] is True
    assert len(auth_client.get("/api/jobs").json()["jobs"]) == 1
    from app.db.session import get_sessionmaker
    from app.models import Application
    with get_sessionmaker()() as db:
        assert db.query(Application).count() == 1


def test_undisclosed_salary_ignores_numbers(auth_client):
    body = {"job_url": "https://careers.example.com/jobs/777", "title": "CS", "salary_min": 9_000_000, "salary_disclosed": False}
    job = auth_client.post("/api/jobs/import", json=body).json()["job"]
    assert job["salary_disclosed"] is False and job["salary_min_monthly"] is None


def test_inverted_salary_rejected(auth_client):
    body = {"job_url": "https://careers.example.com/jobs/99", "title": "X", "salary_min": 10, "salary_max": 1, "salary_disclosed": True}
    assert auth_client.post("/api/jobs/import", json=body).status_code == 422


def test_jobstreet_urls_rejected(auth_client):
    body = {"job_url": "https://id.jobstreet.com/id/job/1", "title": "X"}
    assert auth_client.post("/api/jobs/import", json=body).status_code == 422
