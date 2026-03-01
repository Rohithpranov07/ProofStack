"""Pydantic schemas for the Recruiter Trust Brief Generator.

Request accepts a username.
Response returns a 1-page intelligence brief with strengths, concerns,
recommendation, and engine breakdown.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RecruiterReportRequest(BaseModel):
    """Request body for the recruiter report endpoint."""

    username: str = Field(
        min_length=1,
        max_length=100,
        description="Candidate username to generate a report for",
    )


class RecruiterReportResponse(BaseModel):
    """Deterministic recruiter trust brief."""

    username: str
    pst_score: float = Field(ge=0.0, le=100.0)
    trust_level: str
    strengths: List[str]
    concerns: List[str]
    recommendation: str
    engine_breakdown: Dict[str, Any]
