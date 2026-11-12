"""Browser automation tests: real headless Chromium against local HTML only (mocked environment)."""

from __future__ import annotations

import pytest

from app.services.apply.classify import FormField, classify
from app.services.apply.fields import choose_option, decide
from app.services.apply.policy import allowed_modes
from app.services.apply.runner import run_application
from tests import apply_pages as pages
from tests.matching_fixtures import marketing_profile

playwright = pytest.importorskip("playwright.sync_api")
URL = "https://apply.example.test/job/1"


def profile():
    p = marketing_profile()
    p.personal.full_name = "Fictional Person"
    p.personal.email = "fictional@example.com"
    p.personal.phone = "+62 812 0000 0000"
    p.application_facts.has_work_authorization_indonesia = True
    return p


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture()
def cv(tmp_path):
    f = tmp_path / "cv.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    return str(f)


def page_with(browser, html: str):
    ctx = browser.new_context()
    page = ctx.new_page()
    page.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=html))
    return ctx, page


def run(browser, html, cv, mode="auto", tmp=None, **kw):
    ctx, page = page_with(browser, html)
    try:
        return run_application(page, URL, profile(), {"resume": cv, "cover_letter": None}, mode=mode,
                               screenshot_path=(tmp / "s.png") if tmp else None, confirm_wait_ms=1500, **kw), page
    finally:
        ctx.close()


def test_auto_submits_only_with_confirmation(browser, cv):
    result, _ = run(browser, pages.GOOD_FORM, cv)
    assert result.outcome == "submitted", result
    assert "submitted" in result.confirmation.lower() or "thank you" in result.confirmation.lower()
    assert {"Full name", "Email", "Mobile phone", "Upload CV"} <= set(result.fields_filled)
    assert "Expected salary" not in result.fields_filled  # no verified value -> skipped (optional)


def test_apply_button_opens_form(browser, cv):
    result, _ = run(browser, pages.APPLY_BUTTON_FIRST, cv)
    assert result.outcome == "submitted", result


def test_no_confirmation_is_not_success(browser, cv, tmp_path):
    result, _ = run(browser, pages.NO_CONFIRMATION, cv, tmp=tmp_path)
    assert result.outcome == "stopped" and result.stop_reason == "no_confirmation"
    assert result.screenshot


@pytest.mark.parametrize("html,reason", [
    (pages.UNKNOWN_QUESTION, "unresolved_fields"),
    (pages.LEGAL_CHECKBOX, "unresolved_fields"),
    (pages.SENSITIVE, "unresolved_fields"),
    (pages.CAPTCHA, "captcha_or_bot_check"),
    (pages.LOGIN, "login_required"),
    (pages.CLOSED, "job_closed"),
])
def test_stops_safely(browser, cv, html, reason):
    result, _ = run(browser, html, cv)
    assert result.outcome == "stopped" and result.stop_reason == reason, result
    assert result.confirmation is None


def test_legal_checkbox_is_never_ticked(browser, cv):
    ctx, page = page_with(browser, pages.LEGAL_CHECKBOX)
    try:
        run_application(page, URL, profile(), {"resume": cv}, mode="auto", confirm_wait_ms=500)
        assert page.locator("input[name=decl]").is_checked() is False
        assert "Thank you" not in page.inner_text("body")
    finally:
        ctx.close()


def test_assisted_fills_but_never_submits(browser, cv):
    ctx, page = page_with(browser, pages.UNKNOWN_QUESTION)
    try:
        result = run_application(page, URL, profile(), {"resume": cv}, mode="assisted")
        assert result.outcome == "awaiting_user"
        assert any("Why do you want" in u for u in result.fields_unresolved)
        assert page.locator("#n").input_value() == "Fictional Person"
        assert page.locator("#w").input_value() == "Yes"
        assert "Thank you" not in page.inner_text("body")
    finally:
        ctx.close()


def test_missing_resume_blocks_required_upload(browser):
    result, _ = run(browser, pages.GOOD_FORM, None)
    assert result.stop_reason == "unresolved_fields"
    assert any("Upload CV" in u for u in result.fields_unresolved)


# ---- pure mapping logic ----

@pytest.mark.parametrize("label,ftype,expected", [
    ("Email address", "email", ("mapped", "email")),
    ("No. HP / WhatsApp", "tel", ("mapped", "phone")),
    ("Nama Lengkap", "text", ("mapped", "full_name")),
    ("Gaji yang diharapkan", "text", ("mapped", "expected_salary")),
    ("Current salary", "text", ("salary_history", None)),
    ("Tanggal lahir", "date", ("sensitive", None)),
    ("Agama", "text", ("sensitive", None)),
    ("Saya menyatakan data yang saya isi benar", "checkbox", ("legal", None)),
    ("Unggah CV", "file", ("mapped", "resume")),
    ("Surat lamaran", "file", ("mapped", "cover_letter")),
    ("Tell us about a challenge you solved", "textarea", ("unknown", None)),
    ("What is your email address and why do you want this job?", "textarea", ("unknown", None)),
    ("Are you legally allowed to work in Indonesia?", "select", ("mapped", "work_authorization")),
    ("Bersedia ditempatkan di luar kota?", "select", ("mapped", "relocate")),
    ("Company name of your last employer", "text", ("unknown", None)),
])
def test_classify(label, ftype, expected):
    assert classify(FormField("#x", label, "input", ftype)) == expected


def test_label_wins_over_name_attribute():
    # name="wa" (work authorization) must not be read as WhatsApp/phone.
    f = FormField("#w", "Are you legally allowed to work in Indonesia?", "select", "select", name="wa")
    assert classify(f) == ("mapped", "work_authorization")
    assert classify(FormField("#p", "", "input", "tel", name="phone")) == ("mapped", "phone")


def test_choose_option_never_guesses():
    assert choose_option("Yes", ["Ya", "Tidak"]) == "Ya"
    assert choose_option("No", ["Yes", "No"]) == "No"
    assert choose_option("Yes", ["Maybe", "Later"]) is None
    assert choose_option("Jakarta", ["Jakarta Selatan", "Jakarta Timur"]) is None


def test_missing_fact_blocks_required_field():
    p = profile()
    p.application_facts.expected_salary_monthly_idr = None
    [d] = decide([FormField("#s", "Expected salary", "input", "text", required=True)], p, {})
    assert d.action == "block" and d.value is None


def test_apply_policy():
    assert allowed_modes("https://jobs.lever.co/acme/123/apply") == ["assisted", "auto"]
    assert allowed_modes("https://www.linkedin.com/jobs/view/1") == ["assisted"]  # blocks automation
    assert allowed_modes("https://t.me/lokerjakarta/55") == []                    # a post, not a form
    assert allowed_modes("https://t.me/lokerjakarta/55", "hr@acme.co.id") == ["email"]
    assert allowed_modes("https://jobs.lever.co/acme/1", "hr@acme.co.id") == ["email", "assisted", "auto"]
    assert allowed_modes(None) == []
