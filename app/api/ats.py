"""ATS Resume Intelligence API endpoint.

POST /analyze/ats — Standalone ATS analysis
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ATSResumeAnalysis
from app.db.session import AsyncSessionLocal
from app.schemas.ats import ATSRequest, ATSResponse
from app.services.ats_engine import ATSIntelligenceEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["ats"])


async def _get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/ats", response_model=ATSResponse)
async def analyze_ats(
    request: ATSRequest,
    db: AsyncSession = Depends(_get_db),
) -> ATSResponse:
    """Run standalone ATS intelligence analysis on resume text."""
    engine = ATSIntelligenceEngine()

    result = await engine.analyze(
        username=request.username,
        resume_text=request.resume_text,
        role_level=request.role_level,
        github_languages=request.github_languages,
        github_total_commits=request.github_total_commits,
        product_mindset_score=request.product_mindset_score,
    )

    # Persist to DB
    try:
        db.add(ATSResumeAnalysis(
            username=request.username,
            normalized_score=result["normalized_score"],
            structure_score=result["structure_score"],
            parse_score=result["parse_score"],
            skill_authenticity_score=result["skill_authenticity_score"],
            role_alignment_score=result["role_alignment_score"],
            career_consistency_score=result["career_consistency_score"],
            keyword_stuffing_risk=result["keyword_stuffing_risk"],
            recruiter_readability=result["recruiter_readability"],
            cross_validation_penalty=result.get("cross_validation_penalty", 0.0),
            raw_metrics=result["raw_metrics"],
            explanation=result["explanation"],
        ))
        await db.commit()
    except Exception:
        logger.exception("Failed to save ATS analysis result")
        await db.rollback()

    return ATSResponse(
        username=request.username,
        normalized_score=result["normalized_score"],
        structure_score=result["structure_score"],
        parse_score=result["parse_score"],
        skill_authenticity_score=result["skill_authenticity_score"],
        role_alignment_score=result["role_alignment_score"],
        career_consistency_score=result["career_consistency_score"],
        keyword_stuffing_risk=result["keyword_stuffing_risk"],
        recruiter_readability=result["recruiter_readability"],
        cross_validation_penalty=result.get("cross_validation_penalty", 0.0),
        raw_metrics=result["raw_metrics"],
        explanation=result["explanation"],
        engine_failed=result.get("engine_failed", False),
        failure_reason=result.get("failure_reason"),
    )
