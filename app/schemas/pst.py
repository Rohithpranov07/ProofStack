"""Pydantic schemas for the PST Master Aggregation Engine (Engine 5).

Request accepts a username and role level.
Response returns component scores, final PST score, trust level, and explanation.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class PSTRequest(BaseModel):
    """Request body for the PST aggregation endpoint."""

    username: str = Field(
        min_length=1,
        max_length=100,
        description="Candidate username to aggregate scores for",
    )
    role_level: str = Field(
        description="Target role level: 'entry', 'mid', or 'senior'",
    )


class PSTResponse(BaseModel):
    """Deterministic response from the PST Aggregation Engine."""

    username: str
    role_level: str
    component_scores: Dict[str, Any]
    pst_score: float = Field(ge=0.0, le=100.0)
    trust_level: str
    explanation: Dict[str, Any]
