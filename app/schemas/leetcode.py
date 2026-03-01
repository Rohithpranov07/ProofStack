"""Pydantic schemas for the LeetCode Pattern Intelligence Engine (Engine 3).

Request accepts a LeetCode username.
Response returns deterministic metrics, score, and explanation.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class LeetCodeRequest(BaseModel):
    """Request body for the LeetCode analysis endpoint."""

    username: str = Field(
        min_length=1,
        max_length=100,
        description="LeetCode username to analyze",
    )


class LeetCodeResponse(BaseModel):
    """Deterministic response from the LeetCode Pattern Engine."""

    username: str
    raw_metrics: Dict[str, Any]
    normalized_score: float = Field(ge=0.0, le=100.0)
    explanation: Dict[str, Any]
