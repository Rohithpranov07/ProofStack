"""API router for the Recruiter Trust Brief Generator.

POST /report/recruiter
  Body: { "username": "..." }
  Returns: RecruiterReportResponse (pst_score, trust_level, strengths, concerns, recommendation, engine_breakdown)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RecruiterReport
from app.db.session import AsyncSessionLocal
from app.schemas.report import RecruiterReportRequest, RecruiterReportResponse
from app.services.report_engine import RecruiterReportEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])

engine = RecruiterReportEngine()


async def _get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/recruiter", response_model=RecruiterReportResponse)
async def generate_report(
    body: RecruiterReportRequest,
    db: AsyncSession = Depends(_get_db),
) -> RecruiterReportResponse:
    """Generate a deterministic recruiter trust brief for a candidate."""

    try:
        result = await engine.generate(body.username, db)
    except Exception as exc:
        logger.error("Report generation error for %s: %s", body.username, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Persist to database
    row = RecruiterReport(
        username=body.username,
        report_data=result,
    )
    db.add(row)
    await db.commit()

    return RecruiterReportResponse(**result)
