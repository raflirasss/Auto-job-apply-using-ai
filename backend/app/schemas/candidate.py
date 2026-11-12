"""Structured candidate profile schema.

Every field is optional/empty by default: the system must never invent values.
`missing_information` lists questions the owner must answer through the dashboard.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

ShortStr = Field(default=None, max_length=300)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PersonalInfo(_Model):
    full_name: str | None = ShortStr
    email: str | None = Field(default=None, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=200, description="Current domicile")
    websites: list[str] = Field(default_factory=list, max_length=10)


class Education(_Model):
    institution: str = Field(max_length=300)
    degree: str | None = ShortStr
    field_of_study: str | None = ShortStr
    gpa: float | None = Field(default=None, ge=0)
    gpa_scale: float | None = Field(default=None, gt=0)
    location: str | None = ShortStr
    start_date: str | None = Field(default=None, max_length=30)
    end_date: str | None = Field(default=None, max_length=30)
    is_expected: bool = Field(default=False, description="True when end_date is in the future")


class WorkExperience(_Model):
    company: str = Field(max_length=300)
    title: str | None = ShortStr
    location: str | None = ShortStr
    start_date: str | None = Field(default=None, max_length=30)
    end_date: str | None = Field(default=None, max_length=30)
    employment_type: str | None = Field(default=None, max_length=50)
    responsibilities: list[str] = Field(default_factory=list, max_length=50)


class SkillGroup(_Model):
    category: str = Field(max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=100)


class Language(_Model):
    name: str = Field(max_length=100)
    proficiency: str | None = Field(default=None, max_length=50)


class Certification(_Model):
    name: str = Field(max_length=300)
    issuer: str | None = ShortStr
    date: str | None = Field(default=None, max_length=30)
    credential_url: str | None = Field(default=None, max_length=500)


class Project(_Model):
    name: str = Field(max_length=300)
    description: str | None = Field(default=None, max_length=3000)
    technologies: list[str] = Field(default_factory=list, max_length=50)
    url: str | None = Field(default=None, max_length=500)


class MissingInfo(_Model):
    field: str = Field(max_length=100)
    question: str = Field(max_length=500)
    critical: bool = True


class ApplicationFacts(_Model):
    """Facts commonly requested by application forms. Only filled by the owner."""

    expected_salary_monthly_idr: int | None = Field(default=None, ge=0)
    notice_period: str | None = Field(default=None, max_length=100)
    availability_date: str | None = Field(default=None, max_length=30)
    willing_to_relocate: bool | None = None
    has_work_authorization_indonesia: bool | None = None


class CandidateProfileData(_Model):
    schema_version: Literal[1] = 1
    personal: PersonalInfo = Field(default_factory=PersonalInfo)
    summary: str | None = Field(default=None, max_length=3000)
    education: list[Education] = Field(default_factory=list, max_length=20)
    experience: list[WorkExperience] = Field(default_factory=list, max_length=50)
    skills: list[SkillGroup] = Field(default_factory=list, max_length=30)
    soft_skills: list[str] = Field(default_factory=list, max_length=50)
    languages: list[Language] = Field(default_factory=list, max_length=20)
    certifications: list[Certification] = Field(default_factory=list, max_length=50)
    projects: list[Project] = Field(default_factory=list, max_length=50)
    achievements: list[str] = Field(default_factory=list, max_length=50)
    target_job_categories: list[str] = Field(
        default_factory=list,
        max_length=30,
        description="Owner-selected categories. Only categories supported by the CV evidence.",
    )
    application_facts: ApplicationFacts = Field(default_factory=ApplicationFacts)
    missing_information: list[MissingInfo] = Field(default_factory=list, max_length=50)

    @field_validator("soft_skills", "achievements", "target_job_categories")
    @classmethod
    def _dedupe(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in v:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(item.strip())
        return out


class CandidateProfileOut(_Model):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    version: int
    is_confirmed: bool
    source_cv_id: int | None
    data: CandidateProfileData
    updated_at: str


class CVFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    sha256: str
    mime_type: str
    size_bytes: int
    page_count: int | None
    uploaded_at: str


class CVImportResult(BaseModel):
    cv_file: CVFileOut
    profile: CandidateProfileOut
    duplicate_file: bool
    extraction_warnings: list[str]


_ = HttpUrl  # kept importable for future URL validation needs
