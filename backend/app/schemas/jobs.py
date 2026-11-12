from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ManualJobIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    job_url: str = Field(min_length=15, max_length=1000)
    external_id: str | None = Field(default=None, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    company: str | None = Field(default=None, max_length=300)
    location: str | None = Field(default=None, max_length=300)
    work_arrangement: Literal["onsite", "hybrid", "remote"] | None = None
    employment_type: Literal["full_time", "part_time", "contract", "internship", "freelance", "temporary"] | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_period: Literal["monthly", "annual", "yearly", "weekly", "daily"] = "monthly"
    salary_disclosed: bool = False
    description: str | None = Field(default=None, max_length=30000)
    posted_at: datetime | None = None
    source_note: str | None = Field(default=None, max_length=500)
    apply_url: str | None = Field(default=None, max_length=1000)

    @field_validator("salary_min", "salary_max")
    @classmethod
    def finite_salary(cls, v: float | None) -> float | None:
        if v is not None and v != v:  # NaN
            raise ValueError("Salary must be a finite number")
        return v


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str
    canonical_url: str
    title: str
    company: str | None
    location: str | None
    work_arrangement: str | None
    employment_type: str | None
    salary_min_monthly: float | None
    salary_max_monthly: float | None
    salary_currency: str | None
    salary_disclosed: bool
    description: str | None
    application_url: str | None
    apply_email: str | None = None
    source_note: str | None = None
    posted_at: str | None
    discovered_at: str
    is_available: bool
    match_score: float | None
    match_details: dict | None


class JobImportResult(BaseModel):
    job: JobOut
    duplicate: bool
    note: str
