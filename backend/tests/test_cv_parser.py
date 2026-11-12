from __future__ import annotations

from datetime import date

import pytest

from app.services.cv_parse_utils import parse_date_range
from app.services.cv_parser import parse_cv
from app.services.cv_text import CVExtractionError, extract_cv
from tests.conftest import make_cv_docx, make_cv_pdf


def _parse(content: bytes, name: str = "cv.pdf", today: date = date(2026, 11, 11)):
    _, extracted = extract_cv(name, content)
    return parse_cv(extracted, today=today)


def test_pdf_reorders_headings_and_extracts_personal_info():
    profile, _ = _parse(make_cv_pdf())
    p = profile.personal
    assert p.full_name == "Budi Santoso"
    assert p.email == "budi.santoso@example.com"
    assert p.phone == "+62 812 3456 7890"
    assert p.websites == ["budi.dev"]
    assert p.location is None  # never guessed
    assert profile.summary.startswith("Software engineer")
    assert "team player" in profile.soft_skills and "adaptable" in profile.soft_skills


def test_pdf_education():
    profile, _ = _parse(make_cv_pdf())
    [edu] = profile.education
    assert edu.institution == "Universitas Contoh"
    assert edu.degree == "Bachelor of Computer Science"
    assert edu.field_of_study == "Computer Science"
    assert (edu.gpa, edu.gpa_scale) == (3.75, 4.0)
    assert (edu.start_date, edu.end_date) == ("2018-09", "2022-07")
    assert edu.location == "Jakarta, Indonesia"
    assert edu.is_expected is False


def test_future_graduation_is_flagged():
    profile, _ = _parse(make_cv_pdf(), today=date(2021, 1, 1))
    assert profile.education[0].is_expected is True
    assert any(m.field == "education[0].end_date" for m in profile.missing_information)


def test_pdf_experience_and_wrapped_bullets():
    profile, _ = _parse(make_cv_pdf())
    [exp] = profile.experience
    assert exp.company == "PT Contoh Teknologi"
    assert exp.title == "Backend Developer"
    assert exp.location == "South Jakarta, Indonesia"
    assert (exp.start_date, exp.end_date) == ("2022", "present")
    assert exp.responsibilities == [
        "Built REST APIs with FastAPI and PostgreSQL serving internal tools used by multiple teams.",
        "Wrote automated tests with pytest.",
    ]
    assert exp.employment_type is None


def test_pdf_skills_and_languages():
    profile, _ = _parse(make_cv_pdf())
    groups = {g.category: g.skills for g in profile.skills}
    assert groups["Programming"] == ["Python", "TypeScript", "SQL", "JavaScript"]
    assert groups["Tools"] == ["Git", "Docker"]
    assert [(lang.name, lang.proficiency) for lang in profile.languages] == [
        ("Indonesian", "Native"),
        ("English", "Professional"),
    ]


def test_missing_information_never_invented():
    profile, _ = _parse(make_cv_pdf())
    fields = {m.field for m in profile.missing_information}
    assert {
        "personal.location",
        "application_facts.expected_salary_monthly_idr",
        "application_facts.availability_date",
        "application_facts.has_work_authorization_indonesia",
    } <= fields
    assert profile.application_facts.expected_salary_monthly_idr is None
    assert profile.certifications == [] and profile.projects == []


def test_docx_extraction():
    profile, warnings = _parse(make_cv_docx(), name="cv.docx")
    assert profile.personal.full_name == "Siti Rahma"
    assert profile.personal.phone == "0813-1111-2222"
    [edu] = profile.education
    assert edu.institution == "Politeknik Contoh"
    assert edu.degree == "Diploma III in Accounting"
    assert (edu.start_date, edu.end_date) == ("2017", "2020")
    assert profile.skills[0].skills == ["Microsoft Excel", "Microsoft Word"]
    assert any("DOCX" in w for w in warnings)


def test_rejects_unsupported_files():
    with pytest.raises(CVExtractionError):
        extract_cv("cv.txt", b"hello world")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Feb 2022 – Aug 2026", ("2022-02", "2026-08", False)),
        ("2021 - 2022", ("2021", "2022", False)),
        ("Jan 2023 - Present", ("2023-01", None, True)),
        ("Agustus 2020 - sekarang", ("2020-08", None, True)),
        ("2024", ("2024", "2024", False)),
        ("North Jakarta, Indonesia", None),
    ],
)
def test_date_ranges(text, expected):
    assert parse_date_range(text) == expected
