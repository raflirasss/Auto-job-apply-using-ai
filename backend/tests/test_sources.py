"""Source adapters with a mocked HTTP layer (no network)."""

from __future__ import annotations

import json

import pytest

from app.sources.ats import AtsAdapter
from app.sources.http import Blocked
from app.sources.rss import RssAdapter, parse_feed
from app.sources.telegram import TelegramAdapter, channel_name
from app.sources.telegram_parse import parse_post
from app.sources.text import html_to_text, parse_salary_label
from tests import source_fixtures as fx
from tests.source_helpers import CTX, ISO, RECENT, RFC, client_for


@pytest.mark.parametrize("label,expected", [
    ("Rp 5.000.000 – Rp 7.000.000 per month", (5_000_000, 7_000_000, "monthly")),
    ("Gaji: 4,5 - 5,5 jt", (4_500_000, 5_500_000, "monthly")),
    ("IDR 60.000.000 /year", (60_000_000, 60_000_000, "annual")),
])
def test_salary_labels(label, expected):
    s = parse_salary_label(label)
    assert s.disclosed and (s.min_value, s.max_value, s.period) == expected


@pytest.mark.parametrize("label", ["Gaji menarik", "$3,000 per month", "5.000.000", "Rp 50.000 per jam", None])
def test_ambiguous_salary_is_undisclosed(label):
    assert parse_salary_label(label).disclosed is False


def test_html_to_text_handles_escaped_greenhouse_html():
    assert html_to_text("&lt;p&gt;A&lt;/p&gt;&lt;ul&gt;&lt;li&gt;B&lt;/li&gt;&lt;/ul&gt;") == "A\n• B"


def test_parse_atom_and_rss():
    assert len(parse_feed(fx.GOOGLE_ALERTS_ATOM.replace("{recent}", ISO))) == 2
    assert parse_feed(fx.RSS2.replace("{recent_rfc}", RFC))[0]["link"].startswith("https://jobs.example.com/123")


def test_rss_adapter_unwraps_google_links_and_filters_old_items():
    routes = {"https://www.google.com/alerts/feeds/1/2": (200, fx.GOOGLE_ALERTS_ATOM.replace("{recent}", ISO)),
              "https://loker.example/feed": (200, fx.RSS2.replace("{recent_rfc}", RFC))}
    cfg = {"feeds": [{"name": "Alert", "url": "https://www.google.com/alerts/feeds/1/2"},
                     {"name": "Loker", "url": "https://loker.example/feed"}]}
    res = RssAdapter(client_factory=client_for(routes)).fetch(cfg, CTX)
    assert not res.errors and len(res.jobs) == 2  # the 2020 alert item is filtered out
    alert = res.jobs[0]
    assert alert.url == "https://karir.contoh.co.id/lowongan/admin-marketplace"  # unwrapped from google.com/url
    assert alert.title.startswith("Lowongan Admin Marketplace")
    assert parse_salary_label(alert.salary_label).min_value == 5_000_000


def test_rss_errors_are_reported_not_raised():
    res = RssAdapter(client_factory=client_for({"https://x.example/feed": (403, "")})).fetch(
        {"feeds": [{"name": "X", "url": "https://x.example/feed"}]}, CTX)
    assert res.jobs == [] and "refused" in res.errors[0]


def test_channel_name_normalisation():
    assert channel_name("https://t.me/s/lokerjkt_test") == "lokerjkt_test"
    assert channel_name("@lokerjkt_test") == "lokerjkt_test"
    assert channel_name("bad name!") is None


def test_telegram_preview_parsing_and_filters():
    html = fx.TELEGRAM_PREVIEW.replace("{recent}", ISO)
    res = TelegramAdapter(client_factory=client_for({"https://t.me/s/lokerjkt_test": (200, html)})).fetch(
        {"method": "preview", "channels": ["@lokerjkt_test"]}, CTX)
    assert len(res.jobs) == 2  # the course promo is dropped
    job = res.jobs[0]
    assert (job.title, job.company, job.location) == ("Admin Marketplace", "PT Contoh Niaga", "Jakarta Utara")
    assert job.apply_email == "hrd@contohniaga.co.id" and job.employment_type == "contract"
    assert job.url == "https://t.me/lokerjkt_test/101"
    assert parse_salary_label(job.salary_label).min_value == 4_500_000
    assert any("scam" in n for n in res.jobs[1].notes)


def test_telegram_api_mode_uses_reader():
    msgs = {"lokerjkt_test": [("Lowongan Admin Online Shop\nLokasi: Bekasi\nKirim CV ke hr@x.co.id", 7, RECENT)]}
    adapter = TelegramAdapter(api_reader=lambda cfg, chs, since, lim: msgs)
    res = adapter.fetch({"method": "api", "channels": ["lokerjkt_test"], "api_id": 1, "api_hash": "h", "session": "s"}, CTX)
    assert len(res.jobs) == 1 and res.jobs[0].apply_email == "hr@x.co.id"


def test_parse_post_title_skips_decorations():
    job = parse_post("!!!\n🔥🔥 LOWONGAN KERJA 🔥🔥\nStaff Admin Gudang dibutuhkan segera\nKirim CV ke hr@x.co.id",
                     channel="c", post_id=1, posted_at=None)
    assert job.title == "Staff Admin Gudang dibutuhkan segera"


def test_parse_post_ignores_non_jobs():
    assert parse_post("Selamat pagi semua!", channel="c", post_id=1, posted_at=None) is None


def test_ats_adapter_filters_location_and_maps_fields():
    gh = json.dumps(fx.GREENHOUSE_JSON).replace("{recent}", ISO)
    routes = {"https://api.lever.co/v0/postings/contoh": (200, json.dumps(fx.LEVER_JSON)),
              "https://boards-api.greenhouse.io/v1/boards/contoh/jobs": (200, gh)}
    res = AtsAdapter(client_factory=client_for(routes)).fetch({"lever": ["contoh"], "greenhouse": ["contoh"]}, CTX)
    assert not res.errors, res.errors
    assert [j.title for j in res.jobs] == ["Marketplace Specialist", "Digital Marketing Associate"]  # SG/Manila dropped
    lever = res.jobs[0]
    assert (lever.salary_min, lever.salary_max, lever.work_arrangement) == (6000000, 8000000, "hybrid")
    assert lever.apply_url.endswith("/apply") and "• Shopee" in lever.description
    assert "Facebook Ads" in res.jobs[1].description


def test_robots_txt_is_respected():
    routes = {"https://blocked.example/robots.txt": (200, "User-agent: *\nDisallow: /"),
              "https://blocked.example/jobs": (200, "{}")}
    with client_for(routes)() as http:
        with pytest.raises(Blocked):
            http.get("https://blocked.example/jobs")
