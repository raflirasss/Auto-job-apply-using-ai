from __future__ import annotations

from app.core.logging import redact
from tests.conftest import load_json, make_cv_pdf


def test_health_is_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["database"] is True


def test_endpoints_require_auth(client):
    for path in ("/api/candidate/profile", "/api/settings/preferences", "/api/dashboard/overview"):
        assert client.get(path).status_code == 401


def test_login_throttle(client):
    for _ in range(5):
        assert client.post("/api/auth/login", json={"password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"password": "wrong-password"}).status_code == 429


def test_tampered_token_rejected(client):
    client.cookies.set("ajh_session", "abc.def")
    assert client.get("/api/auth/me").status_code == 401


def test_cv_upload_creates_draft_and_preserves_original(auth_client, env):
    content = make_cv_pdf()
    r = auth_client.post("/api/candidate/cv", files={"file": ("my cv.pdf", content, "application/pdf")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["duplicate_file"] is False
    assert body["profile"]["is_confirmed"] is False
    assert body["profile"]["data"]["personal"]["full_name"] == "Budi Santoso"

    stored = list((env["data_dir"] / "cv" / "originals").iterdir())
    assert len(stored) == 1 and stored[0].read_bytes() == content
    assert load_json(env["config_dir"] / "candidate.json")["personal"]["full_name"] == "Budi Santoso"

    # Re-upload: same file is deduplicated, original untouched, new draft version recorded.
    r2 = auth_client.post("/api/candidate/cv", files={"file": ("again.pdf", content, "application/pdf")})
    assert r2.json()["duplicate_file"] is True
    assert r2.json()["profile"]["version"] == 2
    assert len(list((env["data_dir"] / "cv" / "originals").iterdir())) == 1

    dl = auth_client.get(f"/api/candidate/cv/{body['cv_file']['id']}/download")
    assert dl.status_code == 200 and dl.content == content


def test_cv_upload_rejects_invalid_file(auth_client):
    r = auth_client.post("/api/candidate/cv", files={"file": ("x.pdf", b"not a pdf", "application/pdf")})
    assert r.status_code == 422


def test_profile_edit_and_confirmation_rules(auth_client):
    auth_client.post("/api/candidate/cv", files={"file": ("cv.pdf", make_cv_pdf(), "application/pdf")})
    data = auth_client.get("/api/candidate/profile").json()["profile"]["data"]

    r = auth_client.put("/api/candidate/profile", json={"data": data, "confirm": True})
    assert r.status_code == 422 and "critical" in r.json()["detail"]

    data["personal"]["location"] = "Jakarta Selatan"
    data["application_facts"].update(
        expected_salary_monthly_idr=8000000, availability_date="immediately", has_work_authorization_indonesia=True
    )
    r = auth_client.put("/api/candidate/profile", json={"data": data, "confirm": True})
    assert r.status_code == 200, r.text
    profile = r.json()["profile"]
    assert profile["is_confirmed"] is True
    assert not [m for m in profile["data"]["missing_information"] if m["critical"]]

    versions = auth_client.get("/api/candidate/profile/versions").json()["versions"]
    assert [v["change_source"] for v in versions] == ["confirm", "cv_import"]


def test_profile_rejects_unknown_fields(auth_client):
    auth_client.post("/api/candidate/cv", files={"file": ("cv.pdf", make_cv_pdf(), "application/pdf")})
    data = auth_client.get("/api/candidate/profile").json()["profile"]["data"]
    data["invented_field"] = "x"
    assert auth_client.put("/api/candidate/profile", json={"data": data}).status_code == 422


def test_preferences_roundtrip_and_validation(auth_client, env):
    prefs = auth_client.get("/api/settings/preferences").json()
    assert prefs["minimum_salary"] == 3500000 and prefs["allow_remote"] is False

    prefs["daily_application_limit"] = 5
    assert auth_client.put("/api/settings/preferences", json=prefs).status_code == 200
    assert load_json(env["config_dir"] / "preferences.json")["daily_application_limit"] == 5

    bad = {**prefs, "review_threshold": 90}
    assert auth_client.put("/api/settings/preferences", json=bad).status_code == 422
    remote = {**prefs, "work_arrangement": ["remote"]}
    assert auth_client.put("/api/settings/preferences", json=remote).status_code == 422


def test_ai_key_encrypted_and_masked(auth_client):
    from app.db.session import get_sessionmaker
    from app.models import StoredCredential

    r = auth_client.put("/api/settings/ai", json={"base_url": "https://api.example.com/v1", "model": "m", "api_key": "sk-test-1234567890"})
    body = r.json()
    assert body["api_key_masked"] == "sk-t********7890" and body["configured"] is True
    with get_sessionmaker()() as db:
        assert "sk-test" not in db.get(StoredCredential, "ai_api_key").ciphertext


def test_overview_uses_real_counts(auth_client):
    body = auth_client.get("/api/dashboard/overview").json()
    assert body["jobs_discovered"] == 0 and body["applications_submitted"] == 0
    assert body["success_rate"] is None


def test_log_redaction():
    out = redact("user a.b@example.com phone +62 812 3456 7890 api_key=abc123 Bearer xyz.abc")
    assert "example.com" not in out and "3456" not in out and "abc123" not in out and "xyz" not in out
