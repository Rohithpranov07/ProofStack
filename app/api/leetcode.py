"""API router for Engine 3 — LeetCode Pattern Intelligence.

POST /analyze/leetcode
  Body: { "username": "..." }
  Returns: LeetCodeResponse (raw_metrics, score, explanation)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LeetCodeAnalysis
from app.db.session import AsyncSessionLocal
from app.schemas.leetcode import LeetCodeRequest, LeetCodeResponse
from app.services.leetcode_client import LeetCodeAPIError
from app.services.leetcode_engine import LeetCodeEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["leetcode"])

engine = LeetCodeEngine()


async def _get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/leetcode", response_model=LeetCodeResponse)
async def analyze_leetcode(
    body: LeetCodeRequest,
    db: AsyncSession = Depends(_get_db),
) -> LeetCodeResponse:
    """Analyze a LeetCode profile and return a deterministic trust score."""

    try:
        result = await engine.analyze(body.username)
    except LeetCodeAPIError as exc:
        logger.error("LeetCode API error for %s: %s", body.username, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Persist to database
    row = LeetCodeAnalysis(
        username=result["username"],
        raw_metrics=result["raw_metrics"],
        normalized_score=result["normalized_score"],
        explanation=result["explanation"],
    )
    db.add(row)
    await db.commit()

    return LeetCodeResponse(
        username=result["username"],
        raw_metrics=result["raw_metrics"],
        normalized_score=result["normalized_score"],
        explanation=result["explanation"],
    )
