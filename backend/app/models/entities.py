"""Database schema.

Phase 1 only writes candidate/CV/settings/credential tables. The job, application,
document and agent tables are created now so later phases build on a stable schema;
dashboard statistics are computed from these real tables (empty until data exists).
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow


class ApplicationStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    QUALIFIED = "qualified"
    READY_TO_APPLY = "ready_to_apply"
    APPLIED = "applied"
    PENDING_ACTION = "pending_action"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    FAILED = "failed"


def _enum_values(e: type[enum.Enum]) -> list[str]:
    return [m.value for m in e]


class CVFile(Base):
    """An uploaded original CV. Files are content-addressed and never overwritten."""

    __tablename__ = "cv_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CandidateProfile(Base):
    """The single active candidate profile (one owner per installation)."""

    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)
    source_cv_id: Mapped[int | None] = mapped_column(ForeignKey("cv_files.id"), nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    source_cv: Mapped[CVFile | None] = relationship()
    versions: Mapped[list[CandidateProfileVersion]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="CandidateProfileVersion.version"
    )


class CandidateProfileVersion(Base):
    """Immutable snapshot of every profile change (audit trail)."""

    __tablename__ = "candidate_profile_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(JSON)
    change_source: Mapped[str] = mapped_column(String(50))  # cv_import | manual_edit | confirm
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    profile: Mapped[CandidateProfile] = relationship(back_populates="versions")

    __table_args__ = (UniqueConstraint("profile_id", "version"),)


class AppSetting(Base):
    """Key/value JSON settings (preferences, sources, scheduler). Mirrors config/*.json."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class StoredCredential(Base):
    """Encrypted secrets entered through the dashboard (e.g. AI API key override)."""

    __tablename__ = "stored_credentials"

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    ciphertext: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    external_id: Mapped[str] = mapped_column(String(200))
    canonical_url: Mapped[str] = mapped_column(String(1000), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str | None] = mapped_column(String(300), nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    work_arrangement: Mapped[str | None] = mapped_column(String(30), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    salary_min_monthly: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max_monthly: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    salary_disclosed: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    apply_email: Mapped[str | None] = mapped_column(String(254), nullable=True)  # "send your CV to ..." listings
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (UniqueConstraint("source", "external_id"),)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, values_callable=_enum_values, native_enum=False, length=30),
        default=ApplicationStatus.DISCOVERED,
        index=True,
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_confirmation: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    pending_action: Mapped[str | None] = mapped_column(Text, nullable=True)  # what the owner must do next

    job: Mapped[Job] = relationship()
    history: Mapped[list[ApplicationStatusHistory]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    documents: Mapped[list[Document]] = relationship(back_populates="application")
    attempts: Mapped[list[ApplyAttempt]] = relationship(back_populates="application", cascade="all, delete-orphan")


class ApplyAttempt(Base):
    """One browser-automation run for an application. Never stores passwords or form values."""

    __tablename__ = "apply_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(20))  # assisted | auto
    outcome: Mapped[str] = mapped_column(String(30))  # running | submitted | awaiting_user | stopped | failed
    stop_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    fields_filled: Mapped[list | None] = mapped_column(JSON, nullable=True)  # labels only, no values
    fields_unresolved: Mapped[list | None] = mapped_column(JSON, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped[Application] = relationship(back_populates="attempts")


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"))
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="history")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(30))  # resume | cover_letter | email | answers
    format: Mapped[str] = mapped_column(String(10))  # pdf | docx | txt
    version: Mapped[int] = mapped_column(Integer, default=1)
    stored_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application | None] = relationship(back_populates="documents")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    trigger: Mapped[str] = mapped_column(String(30))  # scheduled | manual
    status: Mapped[str] = mapped_column(String(30))  # running | succeeded | failed | cancelled
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Notification(Base):
    """In-dashboard notifications (always on) plus optional webhook delivery state."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(10), default="info")
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(300), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_webhook: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AgentEvent(Base):
    """Activity log entry shown in the dashboard. Must not contain secrets or PII."""

    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id"), nullable=True)
    level: Mapped[str] = mapped_column(String(10), default="info")
    category: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

