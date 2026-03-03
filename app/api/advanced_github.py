"""API router for the Advanced GitHub Intelligence Engine.

POST /analyze/github-advanced/{username}
  Returns: anomaly metrics, anomaly_score, and behavioral explanation.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdvancedGitHubAnalysis
from app.db.session import AsyncSessionLocal
from app.services.advanced_github_engine import AdvancedGitHubEngine
from app.services.github_client import GitHubAPIError, GitHubRateLimitError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["github-advanced"])

engine = AdvancedGitHubEngine()


async def _get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/github-advanced/{username}")
async def analyze_advanced_github(
    username: str,
    db: AsyncSession = Depends(_get_db),
) -> dict:
    """Run deep behavioral & anomaly detection on a GitHub profile."""

    try:
        result = await engine.analyze(username)
    except GitHubRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except GitHubAPIError as exc:
        logger.error("GitHub API error for %s: %s", username, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Persist to database
    row = AdvancedGitHubAnalysis(
        username=username,
        raw_metrics=result["raw_metrics"],
        anomaly_score=result["anomaly_score"],
        explanation=result["explanation"],
    )
    db.add(row)
    await db.commit()

    return result
