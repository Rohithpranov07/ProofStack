"""SQLAlchemy ORM models for ProofStack.

Tables:
  - github_analysis: Engine 1 — GitHub authenticity analysis results
  - profile_consistency: Engine 2 — Resume ↔ GitHub ↔ LinkedIn consistency results
  - leetcode_analysis: Engine 3 — LeetCode pattern intelligence results
  - red_flag_analysis: Engine 4 — Global red flag detection results
  - product_mindset_analysis: Engine 5 — Product mindset detection results
  - digital_footprint_analysis: Engine 6 — Digital footprint / presence results
  - ats_resume_analysis: Engine 8 — ATS Resume Intelligence results
  - pst_report: Engine 7 — PST master aggregation results
  - recruiter_report: Recruiter Trust Brief reports
  - advanced_github_analysis: Advanced GitHub behavioral & anomaly analysis
  - analysis_job: Async job queue tracking (with analysis_version)

All engine tables carry a ``run_id`` column so that the PST engine
can aggregate results from the *same* pipeline run, avoiding
concurrent contamination.

All engine tables carry ``analysis_version`` so every row can be
traced back to the exact retry / version that produced it.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ShareToken(Base):  # type: ignore[misc]
    """Share tokens for public/read-only dashboard links."""
    __tablename__ = "share_token"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)


class GitHubAnalysis(Base):  # type: ignore[misc]
    __tablename__ = "github_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(39), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    raw_metrics = Column(JSON, nullable=False)
    normalized_score = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ProfileConsistency(Base):  # type: ignore[misc]
    __tablename__ = "profile_consistency"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(39), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    raw_metrics = Column(JSON, nullable=False)
    normalized_score = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class LeetCodeAnalysis(Base):  # type: ignore[misc]
    __tablename__ = "leetcode_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    raw_metrics = Column(JSON, nullable=False)
    normalized_score = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RedFlagAnalysis(Base):  # type: ignore[misc]
    __tablename__ = "red_flag_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    raw_flags = Column(JSON, nullable=False)
    severity_score = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ProductMindsetAnalysis(Base):  # type: ignore[misc]
    __tablename__ = "product_mindset_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    raw_metrics = Column(JSON, nullable=False)
    normalized_score = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class PSTReport(Base):  # type: ignore[misc]
    __tablename__ = "pst_report"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    role_level = Column(String(20), nullable=False)
    component_scores = Column(JSON, nullable=False)
    pst_score = Column(Float, nullable=False)
    trust_level = Column(String(50), nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RecruiterReport(Base):  # type: ignore[misc]
    __tablename__ = "recruiter_report"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    report_data = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AdvancedGitHubAnalysis(Base):  # type: ignore[misc]
    __tablename__ = "advanced_github_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    raw_metrics = Column(JSON, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class DigitalFootprintAnalysis(Base):  # type: ignore[misc]
    __tablename__ = "digital_footprint_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    raw_metrics = Column(JSON, nullable=False)
    normalized_score = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ATSResumeAnalysis(Base):  # type: ignore[misc]
    __tablename__ = "ats_resume_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    analysis_version = Column(Integer, nullable=True)
    normalized_score = Column(Float, nullable=False)
    structure_score = Column(Float, nullable=False)
    parse_score = Column(Float, nullable=False)
    skill_authenticity_score = Column(Float, nullable=False)
    role_alignment_score = Column(Float, nullable=False)
    career_consistency_score = Column(Float, nullable=False)
    keyword_stuffing_risk = Column(String(20), nullable=False)
    recruiter_readability = Column(String(20), nullable=False)
    cross_validation_penalty = Column(Float, nullable=False, default=0.0)
    raw_metrics = Column(JSON, nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserConsent(Base):  # type: ignore[misc]
    """Immutable audit record of user consent before analysis."""
    __tablename__ = "user_consent"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String(36), nullable=False, unique=True, index=True)
    consent_version = Column(String(20), nullable=False)
    consent_text_snapshot = Column(Text, nullable=False)
    consent_given = Column(Boolean, nullable=False, default=False)
    recruiter_confirmation = Column(Boolean, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    jurisdiction_hint = Column(String(10), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AnalysisJob(Base):  # type: ignore[misc]
    __tablename__ = "analysis_job"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String(36), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    result = Column(JSON, nullable=True)
    payload = Column(JSON, nullable=True)
    analysis_version = Column(Integer, nullable=False, default=1)
    consent_recorded = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
