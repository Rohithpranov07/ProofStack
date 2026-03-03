"""GitHub analysis API endpoint.

POST /analyze/github/{username}
  → Runs the GitHubAuthenticityEngine
  → Persists result to PostgreSQL
  → Returns GitHubAnalysisResponse
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GitHubAnalysis
from app.db.session import AsyncSessionLocal
from app.schemas.github import GitHubAnalysisResponse
from app.services.github_auth_engine import GitHubAuthenticityEngine
from app.services.github_client import GitHubAPIError, GitHubRateLimitError

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
    "/analyze/github/{username}",
    response_model=GitHubAnalysisResponse,
    status_code=201,
    summary="Analyze GitHub authenticity for a user",
    responses={
        404: {"description": "GitHub user not found or has no public repos"},
        429: {"description": "GitHub API rate limit exceeded"},
        502: {"description": "GitHub API returned an unexpected error"},
    },
)
async def analyze_github(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> GitHubAnalysisResponse:
    """Run the GitHub Authenticity Engine and persist the result.

    The engine fetches repos, commits, branches, and contributors
    for the given username, computes deterministic metrics, and
    returns a normalized score with a full explanation.
    """
    engine = GitHubAuthenticityEngine()

    try:
        result = await engine.analyze(username)
    except GitHubRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit exceeded. Retry after the reset window.",
        )
    except GitHubAPIError as exc:
        logger.error("GitHub API error during analysis of %s: %s", username, exc)
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API returned HTTP {exc.status_code}.",
        )

    # Persist to PostgreSQL
    record = GitHubAnalysis(
        username=username,
        raw_metrics=result["raw_metrics"],
        normalized_score=result["normalized_score"],
        explanation=result["explanation"],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "Analysis persisted for %s — id=%d, score=%.2f",
        username,
        record.id,
        record.normalized_score,
    )

    return GitHubAnalysisResponse(
        username=result["username"],
        raw_metrics=result["raw_metrics"],
        normalized_score=result["normalized_score"],
        explanation=result["explanation"],
    )
