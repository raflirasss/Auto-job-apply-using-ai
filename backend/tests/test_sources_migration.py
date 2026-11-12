"""An install that saved the old (JobStreet-era) sources format keeps working after the upgrade."""

from app.db.session import get_sessionmaker
from app.models import AppSetting

OLD = {"sources": [{"name": "jobstreet", "enabled": False, "base_url": "https://id.jobstreet.com", "country": "ID",
                    "request_delay_seconds": 5.0, "max_pages_per_search": 3, "notes": "old"}]}


def test_old_sources_row_is_migrated_from_config_file(auth_client):
    with get_sessionmaker()() as db:
        db.merge(AppSetting(key="sources", value=OLD))
        db.commit()
    r = auth_client.get("/api/sources")
    assert r.status_code == 200
    cfg = r.json()["config"]
    assert set(cfg) == {"rss", "telegram", "ats", "fetch_interval_hours"}
    # Values come from config/sources.json (copied into the test config dir), not empty defaults.
    assert cfg["ats"]["enabled"] is True and cfg["ats"]["greenhouse"] == ["xendit"]
    with get_sessionmaker()() as db:
        assert "sources" not in db.get(AppSetting, "sources").value  # stored in the new format


def test_agent_status_works_with_migrated_sources(auth_client):
    with get_sessionmaker()() as db:
        db.merge(AppSetting(key="sources", value=OLD))
        db.commit()
    assert auth_client.get("/api/agent/status").status_code == 200
    assert auth_client.post("/api/agent/start").status_code == 200
