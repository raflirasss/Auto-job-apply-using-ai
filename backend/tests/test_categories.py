from app.schemas.candidate import CandidateProfileData, SkillGroup, WorkExperience
from app.services.categories import category_evidence


def _by_name(profile):
    return {c["category"]: c for c in category_evidence(profile)}


def test_categories_require_evidence():
    profile = CandidateProfileData(
        summary="Experienced in digital marketing and managing Shopee and Tokopedia listings.",
        skills=[SkillGroup(category="Digital Marketing", skills=["Facebook Ads", "Google Ads"])],
    )
    cats = _by_name(profile)
    assert cats["Digital Marketing"]["supported"] is True
    assert cats["Marketplace Administration"]["supported"] is True
    assert cats["Web Development"]["supported"] is False
    assert cats["Software Engineering"]["evidence"] == []
    assert all(c["selected"] is False for c in cats.values())


def test_selection_reflects_profile():
    profile = CandidateProfileData(
        experience=[WorkExperience(company="X", responsibilities=["Handled customer orders via WhatsApp"])],
        target_job_categories=["Customer Service"],
    )
    assert _by_name(profile)["Customer Service"]["selected"] is True


def test_empty_profile_has_no_supported_categories():
    assert not any(c["supported"] for c in category_evidence(CandidateProfileData()))
