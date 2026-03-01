"""ProofStack — Candidate Truth Engine.

FastAPI application entrypoint.
Creates tables on startup and mounts all engine routers.
All endpoints require X-API-Key header except /health and /api/dashboard/shared/{token}.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.github import router as github_router
from app.api.advanced_github import router as advanced_github_router
from app.api.full import router as full_router
from app.api.jobs import router as jobs_router
from app.api.leetcode import router as leetcode_router
from app.api.profile import router as profile_router
from app.api.pst import router as pst_router
from app.api.redflag import router as redflag_router
from app.api.report import router as report_router
from app.api.dashboard import router as dashboard_router
from app.api.dashboard import public_router as dashboard_public_router
from app.api.resume import router as resume_router
from app.api.ats import router as ats_router
from app.api.demo import router as demo_router
from app.core.auth import require_api_key
from app.core.config import settings
from app.db.models import Base
from app.db.session import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="ProofStack",
    description="Candidate Truth Engine — deterministic developer authenticity scoring",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def global_error_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(e),
            },
        )


# ── Protected routes (require X-API-Key) ────────────────
_auth = [Depends(require_api_key)]

app.include_router(github_router, dependencies=_auth)
app.include_router(advanced_github_router, dependencies=_auth)
app.include_router(profile_router, dependencies=_auth)
app.include_router(leetcode_router, dependencies=_auth)
app.include_router(redflag_router, dependencies=_auth)
app.include_router(pst_router, dependencies=_auth)
app.include_router(full_router, dependencies=_auth)
app.include_router(report_router, dependencies=_auth)
app.include_router(dashboard_router, dependencies=_auth)
app.include_router(resume_router, dependencies=_auth)
app.include_router(ats_router, dependencies=_auth)
app.include_router(jobs_router, dependencies=_auth)

# ── Public routes (no auth) ─────────────────────────────
app.include_router(dashboard_public_router)
app.include_router(demo_router)  # demo profiles are public for easy demos


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Deep health check — verifies database, Redis, and GitHub token."""
    import time

    import redis.asyncio as aioredis
    from sqlalchemy import text

    checks: dict[str, Any] = {}
    overall = "ok"

    # Database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        overall = "degraded"

    # Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.close()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        overall = "degraded"

    # GitHub token (check rate limit without consuming a call)
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/rate_limit",
                headers={"Authorization": f"Bearer {settings.GITHUB_TOKEN}"},
                timeout=5.0,
            )
            if resp.status_code == 200:
                remaining = resp.json().get("rate", {}).get("remaining", "?")
                checks["github_token"] = f"ok ({remaining} calls remaining)"
            else:
                checks["github_token"] = f"error: HTTP {resp.status_code}"
                overall = "degraded"
    except Exception as e:
        checks["github_token"] = f"error: {e}"
        overall = "degraded"

    return {
        "status": overall,
        "service": "proofstack",
        "version": app.version,
        "checks": checks,
        "timestamp": time.time(),
    }


@app.get("/metrics", tags=["monitoring"])
async def metrics() -> dict:
    """Operational metrics — job counts by status, engine stats."""
    from sqlalchemy import func, select

    from app.db.models import AnalysisJob
    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            # Job status counts
            status_query = select(
                AnalysisJob.status, func.count()
            ).group_by(AnalysisJob.status)
            result = await db.execute(status_query)
            status_counts = {row[0]: row[1] for row in result.all()}

            # Total jobs
            total_query = select(func.count()).select_from(AnalysisJob)
            total_result = await db.execute(total_query)
            total = total_result.scalar() or 0

        return {
            "jobs": {
                "total": total,
                "by_status": status_counts,
            },
            "engines": {
                "count": 10,
                "names": [
                    "github_authenticity", "advanced_github", "profile_consistency",
                    "leetcode_pattern", "red_flag", "product_mindset",
                    "digital_footprint", "ats_intelligence", "pst_aggregation",
                    "narrative",
                ],
            },
            "version": app.version,
        }
    except Exception as e:
        return {
            "error": str(e),
            "jobs": {"total": 0, "by_status": {}},
            "version": app.version,
        }
