"""API router for Engine 5 — PST Master Aggregation.

POST /analyze/pst
  Body: { "username": "...", "role_level": "entry|mid|senior" }
  Returns: PSTResponse (component_scores, pst_score, trust_level, explanation)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PSTReport
from app.db.session import AsyncSessionLocal
from app.schemas.pst import PSTRequest, PSTResponse
from app.services.pst_engine import PSTAggregationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["pst"])

engine = PSTAggregationEngine()


async def _get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/pst", response_model=PSTResponse)
async def analyze_pst(
    body: PSTRequest,
    db: AsyncSession = Depends(_get_db),
) -> PSTResponse:
    """Aggregate all engine scores into a final ProofStack Trust score."""

    try:
        result = await engine.analyze(body.username, body.role_level, db)
    except Exception as exc:
        logger.error("PST aggregation error for %s: %s", body.username, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Persist to database
    row = PSTReport(
        username=result["username"],
        role_level=result["role_level"],
        component_scores=result["component_scores"],
        pst_score=result["pst_score"],
        trust_level=result["trust_level"],
        explanation=result["explanation"],
    )
    db.add(row)
    await db.commit()

    return PSTResponse(
        username=result["username"],
        role_level=result["role_level"],
        component_scores=result["component_scores"],
        pst_score=result["pst_score"],
        trust_level=result["trust_level"],
        explanation=result["explanation"],
    )
