"""API router for the Async Job Queue System.

POST /jobs/analyze   — Submit a full-analysis job (queued via Celery)
GET  /jobs/{job_id}  — Poll job status and retrieve results
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.consent import CONSENT_TEXT_SNAPSHOT, CONSENT_VERSION
from app.db.models import AnalysisJob, UserConsent
from app.db.session import AsyncSessionLocal
from app.schemas.full_analysis import FullAnalysisRequest
from app.tasks import full_analysis_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@router.post("/analyze")
async def create_analysis_job(
    body: FullAnalysisRequest,
    request: Request,
    db: AsyncSession = Depends(_get_db),
) -> dict:
    """Submit a full-analysis job to the Celery queue.

    Returns immediately with a ``job_id`` and ``status: PENDING``.

    **Consent enforcement (Gate 1 of 3):**
    Analysis CANNOT proceed unless the client supplies a valid consent
    block with ``consent_given=true`` and a matching ``consent_version``.
    """

    # ── Gate 1: Consent validation ──────────────────────────────────
    consent = body.consent

    if not consent.consent_given:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ConsentRequired",
                "message": (
                    "You must accept all required consent checkboxes "
                    "before analysis can begin."
                ),
            },
        )

    if consent.consent_version != CONSENT_VERSION:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ConsentVersionMismatch",
                "message": (
                    f"Expected consent version '{CONSENT_VERSION}', "
                    f"received '{consent.consent_version}'."
                ),
            },
        )

    if body.recruiter_mode and not consent.recruiter_confirmation:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "RecruiterConsentRequired",
                "message": (
                    "Recruiter mode requires confirmation that the candidate "
                    "has given explicit consent for this analysis."
                ),
            },
        )

    # ── Create job ──────────────────────────────────────────────────
    job_id = str(uuid.uuid4())

    task_payload = {
        "username": body.username,
        "role_level": body.role_level,
        "resume_data": body.resume_data.model_dump(mode="json"),
        "linkedin_data": body.linkedin_data.model_dump(mode="json") if body.linkedin_data else None,
        "leetcode_username": body.leetcode_username,
        "resume_text": body.resume_text,
    }

    # Extract audit metadata from the HTTP request
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    user_agent = request.headers.get("user-agent", "unknown")[:500]

    job = AnalysisJob(
        job_id=job_id,
        username=body.username,
        status="PENDING",
        result={},
        payload=task_payload,
        analysis_version=1,
        consent_recorded=True,
    )
    db.add(job)

    # Persist the consent audit record
    consent_record = UserConsent(
        job_id=job_id,
        consent_version=consent.consent_version,
        consent_text_snapshot=CONSENT_TEXT_SNAPSHOT,
        consent_given=True,
        recruiter_confirmation=consent.recruiter_confirmation,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    db.add(consent_record)

    await db.commit()
    await db.refresh(job)

    logger.info(
        "Consent recorded for job %s (version=%s, ip=%s)",
        job_id,
        consent.consent_version,
        client_ip,
    )

    # Dispatch to Celery worker (mode="json" ensures dates/URLs serialize)
    try:
        async_result = full_analysis_task.delay({
            "job_db_id": job.id,
            **task_payload,
        })
        logger.info(
            "Task dispatched for job %s  (celery_id=%s)",
            job_id,
            async_result.id if async_result else "NONE",
        )
    except Exception as exc:
        logger.error("Failed to dispatch Celery task for job %s: %s", job_id, exc)
        # Try once more after a brief pause
        import time; time.sleep(0.3)
        try:
            full_analysis_task.delay({"job_db_id": job.id, **task_payload})
            logger.info("Task dispatched on 2nd attempt for job %s", job_id)
        except Exception as exc2:
            logger.error("2nd dispatch attempt also failed for job %s: %s", job_id, exc2)
            # Mark FAILED so user doesn't sit on a dead PENDING job
            job.status = "FAILED"
            job.result = {"error": f"Task dispatch failed: {exc2}"}
            await db.commit()
            raise HTTPException(
                status_code=503,
                detail="Background worker unreachable — please try again in a moment.",
            )

    return {"job_id": job_id, "status": "PENDING"}


# How many seconds a job can sit as PENDING before we auto-re-dispatch
_PENDING_STUCK_SECONDS = 30
# Track which jobs have been auto-rescued (prevent repeat dispatches every poll)
_auto_rescued: set[str] = set()


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(_get_db),
) -> dict:
    """Poll the status of a previously submitted analysis job.

    If the job has been PENDING for >30 s (task may have been lost) we
    automatically re-dispatch to Celery so the user doesn't have to
    manually click Retry.
    """

    result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.job_id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # ── Auto-rescue stuck PENDING jobs ────────────────────────────
    if job.status == "PENDING" and job.payload and job.created_at:
        from datetime import datetime, timezone

        age = (datetime.now(timezone.utc) - job.created_at).total_seconds()
        if age > _PENDING_STUCK_SECONDS and job_id not in _auto_rescued:
            _auto_rescued.add(job_id)
            logger.warning(
                "Job %s stuck as PENDING for %.0fs — auto-re-dispatching",
                job_id,
                age,
            )
            try:
                full_analysis_task.delay({
                    "job_db_id": job.id,
                    **job.payload,
                })
                logger.info("Auto-rescue dispatch sent for job %s", job_id)
            except Exception as exc:
                logger.error("Auto-rescue dispatch failed for %s: %s", job_id, exc)
    elif job.status != "PENDING":
        # Clean up tracking once job leaves PENDING
        _auto_rescued.discard(job_id)
    # ──────────────────────────────────────────────────────────────

    return {
        "job_id": job_id,
        "status": job.status,
        "analysis_version": job.analysis_version,
        "result": job.result if job.status in ("COMPLETED", "FAILED") else None,
    }


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    db: AsyncSession = Depends(_get_db),
) -> dict:
    """Re-dispatch a stuck PENDING or FAILED job to Celery."""

    result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.job_id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "RUNNING":
        return {"job_id": job_id, "status": job.status, "message": "Job is currently running"}

    if not job.payload:
        raise HTTPException(status_code=400, detail="No payload stored for this job — cannot retry")

    job.status = "PENDING"
    job.result = {}
    job.analysis_version = (job.analysis_version or 0) + 1
    await db.commit()

    full_analysis_task.delay({
        "job_db_id": job.id,
        **job.payload,
    })

    return {
        "job_id": job_id,
        "status": "PENDING",
        "analysis_version": job.analysis_version,
        "message": "Job re-dispatched",
    }
