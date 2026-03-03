"""Profile consistency API endpoint.

POST /analyze/profile-consistency
  → Runs the ProfileConsistencyEngine
  → Persists result to PostgreSQL
  → Returns ProfileConsistencyResponse
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProfileConsistency
from app.db.session import AsyncSessionLocal
from app.schemas.profile import (
    ProfileConsistencyRequest,
    ProfileConsistencyResponse,
)
from app.services.github_client import GitHubAPIError, GitHubRateLimitError
from app.services.profile_consistency_engine import ProfileConsistencyEngine

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield a database session scoped to the request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session  # type: ignore[misc]
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@router.post(
    "/analyze/profile-consistency",
    response_model=ProfileConsistencyResponse,
    status_code=201,
    summary="Cross-verify resume, GitHub, and LinkedIn data",
    responses={
        404: {"description": "GitHub user not found or has no public repos"},
        429: {"description": "GitHub API rate limit exceeded"},
        502: {"description": "GitHub API returned an unexpected error"},
    },
)
async def analyze_profile(
    request: ProfileConsistencyRequest,
    db: AsyncSession = Depends(get_db),
) -> ProfileConsistencyResponse:
    """Run the Profile Consistency Engine and persist the result.

    Accepts structured resume data and optional LinkedIn data,
    cross-verifies against GitHub activity, and returns a
    deterministic consistency score with full explanation.
    """
    engine = ProfileConsistencyEngine()

    try:
        result = await engine.analyze(
            request.username,
            request.resume_data,
            request.linkedin_data,
        )
    except GitHubRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit exceeded. Retry after the reset window.",
        )
    except GitHubAPIError as exc:
        logger.error(
            "GitHub API error during profile analysis of %s: %s",
            request.username,
            exc,
        )
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API returned HTTP {exc.status_code}.",
        )

    # Persist to PostgreSQL
    record = ProfileConsistency(
        username=request.username,
        raw_metrics=result["raw_metrics"],
        normalized_score=result["normalized_score"],
        explanation=result["explanation"],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "Profile consistency persisted for %s — id=%d, score=%.2f",
        request.username,
        record.id,
        record.normalized_score,
    )

    return ProfileConsistencyResponse(
        username=result["username"],
        raw_metrics=result["raw_metrics"],
        normalized_score=result["normalized_score"],
        explanation=result["explanation"],
    )
