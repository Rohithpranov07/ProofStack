"""API router for the Unified Full Analysis Orchestrator.

POST /analyze/full
  Body: FullAnalysisRequest (username, role_level, resume_data, linkedin_data, leetcode_username)
  Returns: Complete Engines 1–5 results in a single response.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.schemas.full_analysis import FullAnalysisRequest
from app.services.full_orchestrator import FullAnalysisOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["full"])


async def _get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/full")
async def full_analysis(
    body: FullAnalysisRequest,
    db: AsyncSession = Depends(_get_db),
) -> dict:
    """Run the complete Engines 1–5 pipeline and return a unified trust report."""

    orchestrator = FullAnalysisOrchestrator()

    try:
        result = await orchestrator.run_full_analysis(
            username=body.username,
            role_level=body.role_level,
            resume_data=body.resume_data,
            linkedin_data=body.linkedin_data,
            leetcode_username=body.leetcode_username,
            db=db,
        )
    except Exception as exc:
        logger.error("Full analysis error for %s: %s", body.username, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result
