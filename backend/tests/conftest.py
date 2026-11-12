from __future__ import annotations

import io
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
TEST_PASSWORD = "test-password-123"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    for name in ("preferences.json", "sources.json", "scheduler.json"):
        shutil.copy(ROOT / "config" / name, config_dir / name)
    monkeypatch.setenv("APP_SECRET_KEY", "x" * 48)
    monkeypatch.setenv("DASHBOARD_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    monkeypatch.setenv("NOTIFY_WEBHOOK_URL", "")
    for var in ("AI_API_KEY", "AI_BASE_URL", "AI_MODEL"):
        monkeypatch.setenv(var, "")

    from app.core import config
    from app.core.security import login_throttle
    from app.db import session

    config.get_settings.cache_clear()
    session.get_engine.cache_clear()
    session.get_sessionmaker.cache_clear()
    login_throttle._failures.clear()

    from app.db.base import Base
    import app.models  # noqa: F401

    Base.metadata.create_all(session.get_engine())
    yield {"tmp": tmp_path, "data_dir": data_dir, "config_dir": config_dir}
    session.get_engine().dispose()
    config.get_settings.cache_clear()
    session.get_engine.cache_clear()
    session.get_sessionmaker.cache_clear()


@pytest.fixture()
def client(env):
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture()
def auth_client(client):
    r = client.post("/api/auth/login", json={"password": TEST_PASSWORD})
    assert r.status_code == 200
    return client


def make_cv_pdf(*, include_dates: bool = True) -> bytes:
    """Synthetic two-column CV (fictional person) mirroring a common layout."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    def text(x, y, s, bold=False):
        page.insert_text((x, y), s, fontname="hebo" if bold else "helv", fontsize=10)

    # Section headings deliberately written *after* their content (as in real exported PDFs).
    text(76, 50, "Budi Santoso", bold=True)
    text(100, 90, "budi.santoso@example.com | +62 812 3456 7890 | budi.dev")
    text(47, 175, "Software engineer with experience building web applications. Team player and")
    text(47, 190, "adaptable, focused on clean code.")
    text(47, 310, "Universitas Contoh", bold=True)
    text(450, 310, "Jakarta, Indonesia")
    text(47, 325, "Bachelor of Computer Science")
    if include_dates:
        # Base-14 fonts cannot encode the en dash; en-dash parsing is covered in test_date_ranges.
        text(440, 325, "Sep 2018 - Jul 2022")
    text(47, 340, "GPA: 3.75/4.00")
    text(47, 405, "PT Contoh Teknologi", bold=True)
    text(430, 405, "South Jakarta, Indonesia")
    text(470, 420, "2022 - Present")
    text(47, 422, "Backend Developer")
    text(66, 450, "• Built REST APIs with FastAPI and PostgreSQL serving internal tools used by multiple")
    text(66, 465, "teams.")
    text(66, 480, "• Wrote automated tests with pytest.")
    text(48, 135, "PROFILE", bold=True)
    text(47, 268, "EDUCATION", bold=True)
    text(47, 365, "WORK EXPERIENCE", bold=True)

    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((48, 50), "SKILLS", fontname="hebo", fontsize=10)
    page2.insert_text((66, 80), "Programming: Python, TypeScript, SQL,", fontname="helv", fontsize=10)
    page2.insert_text((66, 95), "JavaScript", fontname="helv", fontsize=10)
    page2.insert_text((66, 110), "Tools: Git, Docker", fontname="helv", fontsize=10)
    page2.insert_text((66, 125), "Languages: Indonesian (Native), English (Professional)", fontname="helv", fontsize=10)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_cv_docx() -> bytes:
    import docx

    d = docx.Document()
    p = d.add_paragraph()
    p.add_run("Siti Rahma").bold = True
    d.add_paragraph("siti.rahma@example.com | 0813-1111-2222")
    h = d.add_paragraph()
    h.add_run("EDUCATION").bold = True
    e = d.add_paragraph()
    e.add_run("Politeknik Contoh").bold = True
    d.add_paragraph("Diploma III in Accounting\t2017 - 2020")
    h2 = d.add_paragraph()
    h2.add_run("SKILLS").bold = True
    d.add_paragraph("Office: Microsoft Excel, Microsoft Word")
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
