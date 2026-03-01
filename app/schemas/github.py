"""Pydantic response schema for GitHub analysis results.

Every field is explicit and typed — no dynamic dicts in the API contract.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class GitHubAnalysisResponse(BaseModel):
    username: str
    raw_metrics: Dict[str, Any]
    normalized_score: float = Field(ge=0.0, le=100.0)
    explanation: Dict[str, Any]
