from __future__ import annotations

import pytest

from app.services.matching import WEIGHTS
from app.services.matching.location import location_matches
from app.services.matching.requirements import extract_requirements
from tests.matching_fixtures import codes, job, prefs, run


def test_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 6) == 1.0


def test_strong_match_is_auto_apply_eligible():
    r = run()
    assert r["passed_hard_filters"] is True, r["hard_filter_failures"]
    assert r["score"] >= 85, r["components"]
    assert r["recommendation"] == "auto_apply_eligible"
    assert {"Shopee", "Tokopedia", "Canva", "Microsoft Excel"} <= set(r["matching_skills"])
    assert r["relevant_experience"]


def test_result_contains_required_fields():
    r = run()
    for key in ("score", "matching_skills", "missing_skills", "relevant_experience", "concerns",
                "salary", "location", "work_arrangement", "recommendation", "components"):
        assert key in r


@pytest.mark.parametrize("over,code", [
    ({"salary_min_monthly": 2_000_000, "salary_max_monthly": 3_000_000}, "salary_below_minimum"),
    ({"location": "Surabaya"}, "unsupported_location"),
    ({"work_arrangement": "remote"}, "fully_remote"),
    ({"employment_type": "internship"}, "employment_type"),
])
def test_hard_filters(over, code):
    r = run(job(**over))
    assert code in codes(r)
    assert r["recommendation"] == "reject"


def test_salary_range_straddling_minimum_is_not_rejected():
    r = run(job(salary_min_monthly=3_000_000, salary_max_monthly=4_000_000))
    assert "salary_below_minimum" not in codes(r)
    assert r["components"]["salary"]["score"] == 70


def test_missing_mandatory_skill_rejects():
    r = run(job(description="Requirements: wajib menguasai Adobe Photoshop dan Illustrator."))
    assert "missing_mandatory_skills" in codes(r)


def test_incompatible_position_rejects():
    r = run(job(title="Senior Backend Engineer", description="Must have Golang and Docker experience."))
    assert "incompatible_position" in codes(r)
    assert r["recommendation"] == "reject"


def test_years_far_below_requirement_rejects():
    # Profile spans 2021-2024 (~4 years). 10 required -> under half -> hard reject.
    r = run(job(description="Minimum 10 years experience in marketplace. Shopee, Tokopedia."))
    assert "insufficient_experience" in codes(r)


def test_years_slightly_below_requirement_is_concern_only():
    r = run(job(description="Minimum 5 years experience in marketplace. Shopee, Tokopedia."))
    assert "insufficient_experience" not in codes(r)
    assert any("below the stated 5+ years" in c for c in r["concerns"])


def test_remote_signal_in_description_is_detected():
    r = run(job(work_arrangement=None, description="This is a fully remote role. Shopee and Tokopedia."))
    assert r["work_arrangement"] == "remote" and r["work_arrangement_inferred"] is True
    assert "fully_remote" in codes(r)


def test_remote_allowed_when_enabled():
    r = run(job(work_arrangement="remote"), pr=prefs(allow_remote=True, work_arrangement=["remote", "hybrid", "onsite"]))
    assert "fully_remote" not in codes(r)


def test_undisclosed_salary_never_auto_applies():
    r = run(job(salary_disclosed=False, salary_min_monthly=None, salary_max_monthly=None))
    assert r["passed_hard_filters"] is True
    assert r["salary"]["disclosed"] is False
    assert r["components"]["salary"]["score"] == 0
    assert r["recommendation"] == "review"


def test_undisclosed_salary_skipped_when_review_disabled():
    r = run(job(salary_disclosed=False, salary_min_monthly=None, salary_max_monthly=None),
            pr=prefs(allow_undisclosed_salary_review=False))
    assert r["recommendation"] == "skip"


def test_unknown_location_blocks_auto_apply():
    r = run(job(location=None))
    assert r["recommendation"] != "auto_apply_eligible"


def test_duplicate_application_rejects():
    assert "duplicate_application" in codes(run(duplicate_application=True))


def test_unrelated_job_scores_low():
    r = run(job(title="Staff Gudang", description="Mengelola stok gudang dan forklift."))
    assert r["recommendation"] in {"skip", "reject"}
    assert r["score"] < 70


@pytest.mark.parametrize("loc,expected", [
    ("South Jakarta", True), ("Jaksel", True), ("Kota Bekasi, Jawa Barat", True),
    ("BSD City", True), ("Bandung", False), (None, None),
])
def test_location_aliases(loc, expected):
    assert location_matches(loc, ["Jakarta Selatan", "Bekasi", "Tangerang Selatan"]) is expected


def test_requirement_extraction_mandatory_vs_preferred():
    req = extract_requirements("Marketing", "Wajib menguasai Canva.\nNilai tambah: Adobe Photoshop.\nMin. 2 tahun pengalaman di bidang marketing.")
    assert "Canva" in req.mandatory_skills
    assert "Adobe Photoshop" in req.preferred_skills
    assert req.min_years == 2


def test_education_min_level_from_alternatives():
    req = extract_requirements("Admin", "Pendidikan minimal D3/S1 semua jurusan")
    assert req.education_level == 2 and req.education_mandatory is True
