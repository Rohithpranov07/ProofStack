"""API router for Engine 4 — Global Red Flag Detection.

POST /analyze/redflags
  Body: { "username": "...", "github_metrics": {...}, "profile_metrics": {...}, "leetcode_metrics": {...} }
  Returns: RedFlagResponse (raw_flags, severity_score, explanation)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RedFlagAnalysis
from app.db.session import AsyncSessionLocal
from app.schemas.redflag import RedFlagRequest, RedFlagResponse
from app.services.redflag_engine import RedFlagEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["redflags"])

engine = RedFlagEngine()


async def _get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/redflags", response_model=RedFlagResponse)
async def analyze_redflags(
    body: RedFlagRequest,
    db: AsyncSession = Depends(_get_db),
) -> RedFlagResponse:
    """Detect cross-engine red flags and return a deterministic severity score."""

    try:
        result = await engine.analyze(
            body.username,
            body.github_metrics,
            body.profile_metrics,
            body.leetcode_metrics,
        )
    except Exception as exc:
        logger.error("Red flag analysis error for %s: %s", body.username, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Persist to database
    row = RedFlagAnalysis(
        username=result["username"],
        raw_flags=result["raw_flags"],
        severity_score=result["severity_score"],
        explanation=result["explanation"],
    )
    db.add(row)
    await db.commit()

    return RedFlagResponse(
        username=result["username"],
        raw_flags=result["raw_flags"],
        severity_score=result["severity_score"],
        explanation=result["explanation"],
    )
