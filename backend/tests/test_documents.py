from __future__ import annotations

import io
import json

import docx
import pymupdf

from app.services.documents.answers import MANUAL, form_answers
from app.services.documents.content import build_resume, detect_language
from app.services.documents.letters import cover_letter
from tests.matching_fixtures import job, marketing_profile
from tests.test_analysis_api import JOB, confirmed_profile


def test_resume_never_adds_skills_candidate_lacks():
    profile = marketing_profile()
    resume = build_resume(profile, {"Shopee", "Adobe Photoshop", "Python"})
    all_skills = {s for _, g in resume.skill_groups for s in g}
    assert "Adobe Photoshop" not in all_skills and "Python" not in all_skills
    assert "Shopee" in resume.relevant_skills
    assert resume.skill_groups[0][0] == "E-Commerce"  # job-relevant group first
    assert "Adobe Photoshop" not in resume.keywords_used


def test_bullets_reordered_not_changed():
    profile = marketing_profile()
    resume = build_resume(profile, {"Facebook Ads", "Google Ads"})
    first = resume.experience[0]
    assert first.bullets[0] == "Used Facebook Ads and Google Ads."
    assert sorted(first.bullets) == sorted(profile.experience[0].responsibilities)


def test_language_detection_and_letters():
    assert detect_language("Kami mencari kandidat yang memiliki pengalaman dan mampu bekerja") == "id"
    assert detect_language("You must have experience with the team and required skills") == "en"
    profile = marketing_profile()
    profile.personal.full_name = "Fictional Person"
    resume = build_resume(profile, {"Shopee"})
    letter_id = cover_letter(profile, resume, job(), "id")
    assert letter_id[0] == "Dengan hormat," and "Admin Marketplace" in letter_id[1]
    assert letter_id[-1].endswith("Fictional Person")
    letter_en = cover_letter(profile, resume, job(company=None), "en")
    assert "your company" in letter_en[1]


def test_form_answers_mark_missing_facts():
    profile = marketing_profile()
    answers = {a["key"]: a for a in form_answers(profile, build_resume(profile, set()))}
    assert answers["expected_salary"]["answer"] == MANUAL and answers["expected_salary"]["source"] == "missing"
    assert answers["work_authorization"]["source"] == "missing"
    profile.application_facts.expected_salary_monthly_idr = 7_500_000
    profile.application_facts.has_work_authorization_indonesia = True
    answers = {a["key"]: a for a in form_answers(profile, build_resume(profile, set()))}
    assert answers["expected_salary"]["answer"] == "7.500.000"
    assert answers["work_authorization"]["answer"] == "Yes"


def test_generate_documents_end_to_end(auth_client, env):
    assert auth_client.post("/api/jobs/1/documents").status_code == 404
    job_id = auth_client.post("/api/jobs/import", json=JOB).json()["job"]["id"]
    assert auth_client.post(f"/api/jobs/{job_id}/documents").status_code == 409  # profile not confirmed
    confirmed_profile(auth_client)

    r = auth_client.post(f"/api/jobs/{job_id}/documents", json={"template": "modern"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["version"] == 1 and len(body["documents"]) == 6
    assert {(d["kind"], d["format"]) for d in body["documents"]} == {
        ("resume", "pdf"), ("resume", "docx"), ("cover_letter", "pdf"), ("cover_letter", "docx"), ("email", "txt"), ("answers", "json")}

    by = {(d["kind"], d["format"]): d["id"] for d in body["documents"]}
    pdf = auth_client.get(f"/api/documents/{by[('resume', 'pdf')]}/download")
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"
    text = "".join(p.get_text() for p in pymupdf.open(stream=pdf.content, filetype="pdf"))
    assert "Budi Santoso" in text and "PT Contoh Teknologi" in text  # real, selectable text (ATS)

    d = docx.Document(io.BytesIO(auth_client.get(f"/api/documents/{by[('resume', 'docx')]}/download").content))
    assert any("Budi Santoso" in p.text for p in d.paragraphs)
    answers = json.loads(auth_client.get(f"/api/documents/{by[('answers', 'json')]}/download").content)
    assert {a["key"] for a in answers} >= {"full_name", "expected_salary"}

    # New version, old version kept
    assert auth_client.post(f"/api/jobs/{job_id}/documents").json()["version"] == 2
    assert len(auth_client.get("/api/documents").json()["documents"]) == 12
    assert auth_client.post(f"/api/jobs/{job_id}/documents", json={"template": "nope"}).status_code == 422


def test_pdf_handles_unencodable_characters(tmp_path):
    from app.services.documents.render_pdf import render_resume_pdf
    from app.services.documents.templates import get_template

    profile = marketing_profile()
    profile.personal.full_name = "Name 🚀 <script>"
    resume = build_resume(profile, set())
    out = tmp_path / "x.pdf"
    render_resume_pdf(resume, "en", get_template(None), out)
    text = "".join(p.get_text() for p in pymupdf.open(out))
    assert "Name" in text and "<script>" in text
