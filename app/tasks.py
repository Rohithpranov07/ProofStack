"""Celery tasks for ProofStack.

Wraps the async FullAnalysisOrchestrator in a synchronous Celery task
by running the coroutine via ``asyncio.run()``.

The task updates the AnalysisJob row through its lifecycle:
    PENDING → RUNNING → COMPLETED | FAILED

**Gate 2 of 3:** Before executing any engine work the worker verifies
that a UserConsent record exists for the job.  If consent is missing the
job is marked FAILED immediately.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.models import AnalysisJob, UserConsent
from app.db.session import AsyncSessionLocal
from app.schemas.profile import LinkedInStructured, ResumeStructured
from app.services.full_orchestrator import FullAnalysisOrchestrator

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.full_analysis_task")
def full_analysis_task(payload: Dict[str, Any]) -> None:
    """Execute the full Engines 1–5 pipeline as a background Celery task.

    ``payload`` keys:
        job_db_id, username, role_level, resume_data, linkedin_data, leetcode_username
    """

    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            orchestrator = FullAnalysisOrchestrator()

            # Mark job as RUNNING
            job = await db.get(AnalysisJob, payload["job_db_id"])
            if job is None:
                return

            # Guard: if already RUNNING or COMPLETED, skip (duplicate dispatch)
            if job.status in ("RUNNING", "COMPLETED"):
                logger.info(
                    "Task for job DB id %s already %s — skipping duplicate",
                    payload["job_db_id"],
                    job.status,
                )
                return

            # ── Gate 2: Consent enforcement (worker level) ──────────
            if not job.consent_recorded:
                logger.error(
                    "Consent gate failed (worker) for job DB id %s — "
                    "consent_recorded is False",
                    payload["job_db_id"],
                )
                job.status = "FAILED"
                job.result = {
                    "error": "ConsentNotRecorded",
                    "message": (
                        "Analysis blocked: no consent record found. "
                        "This job cannot proceed."
                    ),
                }
                await db.commit()
                return

            # Double-check: verify the UserConsent row actually exists
            consent_row = (
                await db.execute(
                    select(UserConsent).where(
                        UserConsent.job_id == job.job_id
                    )
                )
            ).scalar_one_or_none()

            if consent_row is None:
                logger.error(
                    "Consent gate failed (worker) for job %s — "
                    "UserConsent row missing",
                    job.job_id,
                )
                job.status = "FAILED"
                job.result = {
                    "error": "ConsentNotRecorded",
                    "message": (
                        "Analysis blocked: consent audit record missing. "
                        "This job cannot proceed."
                    ),
                }
                await db.commit()
                return
            # ── End Gate 2 ──────────────────────────────────────────

            job.status = "RUNNING"
            await db.commit()

            try:
                # Reconstruct Pydantic models from serialised dicts
                resume_data = ResumeStructured(**payload["resume_data"])
                linkedin_data = (
                    LinkedInStructured(**payload["linkedin_data"])
                    if payload.get("linkedin_data")
                    else None
                )

                result = await orchestrator.run_full_analysis(
                    username=payload["username"],
                    role_level=payload["role_level"],
                    resume_data=resume_data,
                    linkedin_data=linkedin_data,
                    leetcode_username=payload["leetcode_username"],
                    resume_text=payload.get("resume_text"),
                    db=db,
                    analysis_version=job.analysis_version if job else 1,
                    job_id=job.job_id,
                )

                job.status = "COMPLETED"
                job.result = result
                await db.commit()

            except Exception as exc:
                await db.rollback()
                job.status = "FAILED"
                job.result = {"error": str(exc)}
                await db.commit()

    asyncio.run(_run())
