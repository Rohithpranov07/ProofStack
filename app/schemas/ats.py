"""Pydantic schemas for the ATS Resume Intelligence Engine.

Request/Response models for Engine 8 — Advanced ATS Intelligence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ATSExperienceBlock(BaseModel):
    """Extracted experience block from resume."""
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullet_points: List[str] = Field(default_factory=list)


class ATSParsedResume(BaseModel):
    """ATS-simulated parsed resume output."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ATSExperienceBlock] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class ATSRequest(BaseModel):
    """Request body for standalone ATS analysis."""
    username: str = Field(min_length=2, max_length=100)
    role_level: str = Field(default="mid")
    resume_text: str = Field(min_length=10)
    github_languages: List[str] = Field(default_factory=list)
    github_repo_count: int = Field(default=0)
    github_total_commits: int = Field(default=0)
    product_mindset_score: float = Field(default=0.0)


class ATSResponse(BaseModel):
    """Response from the ATS intelligence engine."""
    username: str
    normalized_score: float
    structure_score: float
    parse_score: float
    skill_authenticity_score: float
    role_alignment_score: float
    career_consistency_score: float
    keyword_stuffing_risk: str
    recruiter_readability: str
    cross_validation_penalty: float
    raw_metrics: Dict[str, Any]
    explanation: Dict[str, Any]
    engine_failed: bool = False
    failure_reason: Optional[str] = None
