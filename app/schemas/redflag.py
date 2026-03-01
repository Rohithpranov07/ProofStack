"""Pydantic schemas for the Global Red Flag Detection Engine (Engine 4).

Request accepts a username plus raw metrics from Engines 1-3.
Response returns detected flags, severity score, and explanation.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class RedFlagRequest(BaseModel):
    """Request body for the red-flag analysis endpoint."""

    username: str = Field(
        min_length=1,
        max_length=100,
        description="Candidate username to analyze",
    )
    github_metrics: Dict[str, Any] = Field(
        description="Raw metrics from Engine 1 (GitHub Authenticity)",
    )
    profile_metrics: Dict[str, Any] = Field(
        description="Raw metrics from Engine 2 (Profile Consistency)",
    )
    leetcode_metrics: Dict[str, Any] = Field(
        description="Raw metrics from Engine 3 (LeetCode Pattern)",
    )


class RedFlagResponse(BaseModel):
    """Deterministic response from the Red Flag Detection Engine."""

    username: str
    raw_flags: Dict[str, Any]
    severity_score: float = Field(ge=0.0, le=100.0)
    explanation: Dict[str, Any]
