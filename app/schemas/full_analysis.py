"""Pydantic schema for the Unified Full Analysis Orchestrator.

Request accepts all inputs needed for Engines 1–5 in a single call,
plus the mandatory consent block.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


from app.schemas.profile import LinkedInStructured, ResumeStructured

# GitHub usernames: alphanumeric + hyphens, 1-39 chars, no leading/trailing hyphen
_GITHUB_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$")
# LeetCode usernames: alphanumeric + underscores/hyphens
_LEETCODE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,98}[a-zA-Z0-9]$")


class ConsentPayload(BaseModel):
    """Consent data that MUST accompany every analysis request."""

    consent_version: str = Field(
        min_length=1,
        description="Consent version string, e.g. 'v1.0.0'",
    )
    consent_given: bool = Field(
        description="Must be true — user accepted all required checkboxes",
    )
    recruiter_confirmation: Optional[bool] = Field(
        default=None,
        description="Required true when submitting in recruiter mode",
    )


class FullAnalysisRequest(BaseModel):
    """Request body for the full-analysis endpoint."""

    username: str = Field(
        min_length=2,
        max_length=100,
        description="GitHub username (used for Engines 1, 2, 4, 5)",
    )
    role_level: str = Field(
        description="Target role level: 'entry', 'mid', or 'senior'",
    )
    resume_data: ResumeStructured = Field(
        description="Structured resume data for Engine 2",
    )
    linkedin_data: Optional[LinkedInStructured] = Field(
        default=None,
        description="Optional LinkedIn profile data for Engine 2",
    )
    leetcode_username: Optional[str] = Field(
        default=None,
        max_length=100,
        description="LeetCode username for Engine 3 (optional)",
    )
    resume_text: Optional[str] = Field(
        default=None,
        description="Raw resume text for ATS Intelligence Engine (Engine 8)",
    )
    consent: ConsentPayload = Field(
        description="Mandatory consent block — analysis cannot proceed without it",
    )
    recruiter_mode: Optional[bool] = Field(
        default=False,
        description="Whether submission is from a recruiter",
    )

    # GitHub usernames: alphanumeric + hyphens, 1-39 chars, no leading/trailing hyphen
    # LeetCode usernames: alphanumeric + underscores/hyphens

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not _GITHUB_RE.match(v):
            raise ValueError(
                "Invalid GitHub username — must be 1-39 alphanumeric/hyphen chars, "
                "no leading/trailing hyphens"
            )
        return v

    @field_validator("leetcode_username")
    @classmethod
    def validate_leetcode_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not _LEETCODE_RE.match(v):
            raise ValueError(
                "Invalid LeetCode username — alphanumeric, underscores, hyphens only"
            )
        return v

    @field_validator("role_level")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = ["entry", "mid", "senior"]
        if v not in allowed:
            raise ValueError(f"Invalid role_level. Must be one of {allowed}")
        return v
