"""Fictional profile/job fixtures for matching tests (no real personal data)."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.schemas.candidate import CandidateProfileData, Education, Language, SkillGroup, WorkExperience
from app.schemas.settings import Preferences
from app.services.matching import evaluate

TODAY = date(2026, 11, 11)


def prefs(**over) -> Preferences:
    base = dict(
        location=["Jakarta", "Jakarta Selatan", "Jakarta Timur", "Tangerang Selatan", "Bekasi", "Depok"],
        work_arrangement=["hybrid", "onsite"], employment_types=["full_time", "contract"],
        minimum_salary=3_500_000, lookback_days=7, minimum_match_score=85, review_threshold=70,
        auto_apply=True, daily_application_limit=10,
    )
    return Preferences(**{**base, **over})


def marketing_profile() -> CandidateProfileData:
    return CandidateProfileData(
        summary="Graduate with marketplace and digital marketing experience.",
        education=[Education(institution="Uni X", degree="Bachelor of Informatics Engineering", end_date="2026-08")],
        experience=[
            WorkExperience(company="A", title="Marketplace & E-Commerce", start_date="2023", end_date="2024", responsibilities=[
                "Managed product listings on Shopee and Tokopedia.",
                "Created social media content and short-form video with CapCut.",
                "Used Facebook Ads and Google Ads.",
            ]),
            WorkExperience(company="B", title="Online Customer Service", start_date="2021", end_date="2022", responsibilities=[
                "Handled customer orders via WhatsApp.",
            ]),
        ],
        skills=[
            SkillGroup(category="Digital Marketing", skills=["Social Media Marketing", "Content Creation", "Copywriting", "Facebook Ads", "Google Ads"]),
            SkillGroup(category="E-Commerce", skills=["Shopee", "Tokopedia", "Product Listing", "Catalog Management"]),
            SkillGroup(category="Creative", skills=["Canva", "CapCut"]),
            SkillGroup(category="Data", skills=["Microsoft Excel", "Google Sheets"]),
        ],
        languages=[Language(name="English", proficiency="Intermediate")],
        target_job_categories=["Marketplace Administration", "Digital Marketing"],
    )


def job(**over):
    base = dict(
        title="Admin Marketplace", company="PT Contoh", location="Jakarta Selatan",
        work_arrangement="onsite", employment_type="full_time",
        salary_min_monthly=5_000_000, salary_max_monthly=6_000_000, salary_disclosed=True,
        description=(
            "Requirements:\n- Minimal S1 semua jurusan\n- Wajib menguasai Shopee dan Tokopedia\n"
            "- Mampu membuat konten dengan Canva\n- Familiar with Microsoft Excel\n- Fresh graduate welcome"
        ),
    )
    return SimpleNamespace(**{**base, **over})


def run(j=None, p=None, pr=None, **kw) -> dict:
    return evaluate(j or job(), p or marketing_profile(), pr or prefs(), today=TODAY, **kw)


def codes(result: dict) -> set[str]:
    return {f["code"] for f in result["hard_filter_failures"]}
