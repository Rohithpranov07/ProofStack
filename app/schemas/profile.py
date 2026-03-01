"""Pydantic schemas for the Profile Consistency Engine (Engine 2).

Defines structured input for resume data, LinkedIn data,
and the deterministic response contract.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class SkillItem(BaseModel):
    """A single skill claimed on the resume with years of experience."""

    name: str
    years: float = Field(ge=0.0, description="Claimed years of experience")


class ProjectItem(BaseModel):
    """A project listed on the resume."""

    name: str
    github_url: Optional[str] = None
    description: Optional[str] = None


class ExperienceItem(BaseModel):
    """A single work-experience entry."""

    company: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class LinkedInStructured(BaseModel):
    """Structured LinkedIn profile data provided by the caller.

    No scraping — the caller supplies this from their own parsing pipeline.
    """

    headline: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[ExperienceItem]] = None
    profile_url: Optional[HttpUrl] = None


class ResumeStructured(BaseModel):
    """Structured resume data provided by the caller."""

    skills: List[SkillItem]
    projects: List[ProjectItem]
    experience: List[ExperienceItem]


class ProfileConsistencyRequest(BaseModel):
    """Request body for the profile-consistency endpoint."""

    username: str = Field(
        min_length=1,
        max_length=39,
        description="GitHub username to cross-verify",
    )
    resume_data: ResumeStructured
    linkedin_data: Optional[LinkedInStructured] = None


class ProfileConsistencyResponse(BaseModel):
    """Deterministic response from the Profile Consistency Engine."""

    username: str
    raw_metrics: Dict[str, Any]
    normalized_score: float = Field(ge=0.0, le=100.0)
    explanation: Dict[str, Any]
