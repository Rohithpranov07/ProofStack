"""Dashboard aggregation endpoint.

GET /api/dashboard/{job_id}
  Returns the full dashboard payload for the recruiter intelligence console.
  Builds the response directly from the AnalysisJob.result JSON column,
  which already contains all engine outputs — no run_id scoping needed.

GET /api/dashboard/{job_id}/pdf
  Generates a PDF report (HTML → WeasyPrint).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AnalysisJob, ShareToken
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
public_router = APIRouter(prefix="/api/dashboard", tags=["dashboard-public"])


# ── DB dependency ─────────────────────────────────────────
async def _get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# ── Helpers ───────────────────────────────────────────────
def _d(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safely drill into nested dicts."""
    current = obj
    for k in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(k, default)
    return current if current is not None else default


def _entropy_label(entropy_value: Any) -> str:
    """Convert numeric entropy to a human-readable label."""
    try:
        e = float(entropy_value or 0)
    except (ValueError, TypeError):
        return "N/A"
    if e >= 4.0:
        return "High"
    if e >= 2.5:
        return "Medium"
    if e > 0:
        return "Low"
    return "N/A"


# ── Main endpoint ─────────────────────────────────────────
@router.get("/{job_id}")
async def get_dashboard(
    job_id: str,
    db: AsyncSession = Depends(_get_db),
) -> Dict[str, Any]:
    """Aggregate all engine results into the dashboard response shape.

    Reads everything from AnalysisJob.result (single query) so it works
    regardless of whether engine tables have a run_id column.
    """

    # 1. Load the job
    result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.job_id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail=f"Job status is {job.status} — dashboard requires COMPLETED",
        )

    job_result: Dict[str, Any] = job.result or {}
    if not job_result:
        raise HTTPException(status_code=422, detail="Completed job has empty result")

    username: str = job.username
    run_id: str = job_result.get("run_id", job_id)  # fallback to job_id
    role_level: str = job_result.get("role_level", "mid")

    # 2. Extract engine sub-dicts directly from job.result
    gh_data = job_result.get("github", {}) or {}
    adv_data = job_result.get("advanced_github", {}) or {}
    profile_data = job_result.get("profile_consistency", {}) or {}
    lc_data = job_result.get("leetcode", {}) or {}
    rf_data = job_result.get("redflags", {}) or {}
    pst_data = job_result.get("pst_report", {}) or {}
    pm_data = job_result.get("product_mindset", {}) or {}
    df_data = job_result.get("digital_footprint", {}) or {}
    ats_data = job_result.get("ats_intelligence", {}) or {}
    report_data = job_result.get("recruiter_report", {}) or {}

    gh_metrics = gh_data.get("raw_metrics", {}) or {}
    gh_expl = gh_data.get("explanation", {}) or {}
    adv_metrics = adv_data.get("raw_metrics", {}) or {}
    profile_metrics = profile_data.get("raw_metrics", {}) or {}
    lc_metrics = lc_data.get("raw_metrics", {}) or {}
    lc_expl = lc_data.get("explanation", {}) or {}
    pm_metrics = pm_data.get("raw_metrics", {}) or {}
    pm_expl = pm_data.get("explanation", {}) or {}
    df_metrics = df_data.get("raw_metrics", {}) or {}
    df_expl = df_data.get("explanation", {}) or {}
    ats_metrics = ats_data.get("raw_metrics", {}) or {}
    ats_expl = ats_data.get("explanation", {}) or {}
    rf_flags = rf_data.get("raw_flags", {}) or {}
    pst_expl = pst_data.get("explanation", {}) or {}
    pst_comp = pst_data.get("component_scores", {}) or {}
    report_payload = report_data.get("report_data", report_data) or {}

    # 3. Build profile verification items from raw_metrics
    verification_items = _build_verification_items(profile_metrics)

    # Build commit timeline from github raw_metrics
    commit_timeline = _build_commit_timeline(gh_metrics, gh_data)

    # Build leetcode difficulty bars
    lc_easy = int(lc_metrics.get("easy", 0))
    lc_medium = int(lc_metrics.get("medium", 0))
    lc_hard = int(lc_metrics.get("hard", 0))

    # Build leetcode trend
    leetcode_trend = _build_leetcode_trend(lc_metrics)

    # Escalation info
    escalation = {
        "cap_applied": pst_expl.get("cap_applied"),
        "escalation_reasons": pst_expl.get("escalation_reasons", []),
        "anomaly_score": pst_expl.get("anomaly_score", 0.0),
        "confidence_reduction_pct": pst_expl.get("confidence_reduction_pct", 0.0),
    }

    # Determine engine failure from job result
    engine_failures: List[str] = job_result.get("engine_failures", [])

    # PST scores
    pst_score = float(pst_data.get("pst_score", 0) or 0)
    trust_level = pst_data.get("trust_level", "No Data") or "No Data"

    # PST component scores breakdown
    pst_components = {
        "github_score": float(pst_comp.get("github_score", 0) or 0),
        "profile_score": float(pst_comp.get("profile_score", 0) or 0),
        "leetcode_score": float(pst_comp.get("leetcode_score", 0) or 0),
        "redflag_severity": float(pst_comp.get("redflag_severity", 0) or 0),
    }

    # PST weighting info
    pst_weights = pst_expl.get("weighting_used", {}) or {}
    pst_penalty = float(pst_expl.get("penalty_deduction", 0) or 0)

    # ── Derive ATS sub-metrics from nested detail dicts ──
    _struct_d = ats_metrics.get("structure_detail", {})
    _read_d = ats_metrics.get("readability_detail", {})
    _skill_d = ats_metrics.get("skill_detail", {})

    # section_completeness: use engine value or derive from sections data
    _sec_comp = _struct_d.get("section_completeness")
    if _sec_comp is None:
        _sf = set(_struct_d.get("sections_found", []))
        _required = {"experience", "skills", "education"}
        _recommended = {"summary", "contact", "projects"}
        _found_req = len(_required.intersection(_sf))
        _found_rec = len(_recommended.intersection(_sf))
        _sec_comp = (_found_req / 3) * (20 / 30) + (_found_rec / 3) * (10 / 30) if _sf else 0

    # bullet_quality: use engine value or derive from verb/passive/length data
    _bq = _struct_d.get("bullet_quality")
    if _bq is None:
        _vlr = _struct_d.get("verb_led_ratio", 0) or 0
        _pvr = _struct_d.get("passive_voice_ratio", 0) or 0
        _abl = _struct_d.get("avg_bullet_length", 0) or 0
        _bq = _vlr * 0.4 + (1 - _pvr) * 0.3
        if 50 <= _abl <= 150:
            _bq += 0.3
        elif 30 <= _abl <= 200:
            _bq += 0.18
        elif _abl > 0:
            _bq += 0.06
        _bq = min(1.0, _bq)

    # formatting_safety: use engine value or derive from tables/columns/word_count
    _fs = _struct_d.get("formatting_safety")
    if _fs is None:
        _fmt = 20.0
        if _struct_d.get("has_tables"):
            _fmt -= 5
        if _struct_d.get("has_columns"):
            _fmt -= 5
        if (_struct_d.get("word_count", 500) or 500) < 100:
            _fmt -= 10
        _fs = max(0, _fmt) / 20.0

    return {
        "job_id": job_id,
        "run_id": run_id,
        "username": username,
        "role_level": role_level,
        "trust_score": pst_score,
        "trust_band": trust_level,
        "escalation": escalation,
        "pst_components": pst_components,
        "pst_weights": pst_weights,
        "pst_penalty": pst_penalty,
        "engines": {
            "github": {
                "normalized_score": float(gh_data.get("normalized_score", 0) or 0),
                "consistency": float(gh_metrics.get("structural_consistency", gh_metrics.get("commit_variance", 0)) or 0),
                "entropy": float(gh_metrics.get("commit_message_entropy", 0) or 0),
                "entropy_label": gh_expl.get("entropy_label", _entropy_label(gh_metrics.get("commit_message_entropy", 0))),
                "commit_count": int(gh_metrics.get("total_commits", 0)),
                "repo_count": int(gh_metrics.get("total_repositories", gh_metrics.get("repos_analyzed", 0))),
                "burst_detected": bool(gh_metrics.get("burst_flag", gh_expl.get("burst_detected", False))),
                "avg_branches": float(gh_metrics.get("average_branches", 0) or 0),
                "avg_contributors": float(gh_metrics.get("average_contributors", 0) or 0),
                "avg_repo_age_days": float(gh_metrics.get("average_repo_age_days", 0) or 0),
                "engine_failed": "github" in engine_failures,
                "failure_reason": _get_failure_reason(job_result, "github"),
                "rate_limited": _get_rate_limited(job_result, "github"),
            },
            "advanced_github": {
                "anomaly_score": float(adv_data.get("anomaly_score", 0) or 0),
                "loc_anomaly_ratio": float(adv_metrics.get("loc_anomaly_ratio", 0) or 0),
                "interval_cv": float(adv_metrics.get("interval_cv", 0) or 0),
                "empty_commit_ratio": float(adv_metrics.get("empty_commit_ratio", 0) or 0),
                "repetitive_message_ratio": float(adv_metrics.get("repetitive_message_ratio", 0) or 0),
                "total_commits_inspected": int(adv_metrics.get("total_commits_inspected", 0)),
                "engine_failed": "advanced_github" in engine_failures,
            },
            "profile": {
                "normalized_score": float(profile_data.get("normalized_score", 0) or 0),
                "has_data": bool(profile_metrics),
                "skill_ratio": profile_metrics.get("skill_ratio", 0),
                "project_ratio": profile_metrics.get("project_ratio", 0),
                "experience_ratio": profile_metrics.get("experience_ratio", 0),
                "verification_items": verification_items,
                "skill_verified": int(profile_metrics.get("skill_verified", 0)),
                "skill_total": int(profile_metrics.get("skill_total", 0)),
                "skill_mismatches": profile_metrics.get("skill_mismatches", []),
                "project_verified": int(profile_metrics.get("project_verified", 0)),
                "project_total": int(profile_metrics.get("project_total", 0)),
                "project_mismatches": profile_metrics.get("project_mismatches", []),
                "experience_verified": int(profile_metrics.get("experience_verified", 0)),
                "experience_total": int(profile_metrics.get("experience_total", 0)),
                "experience_mismatches": profile_metrics.get("experience_mismatches", []),
                "earliest_github_repo_date": profile_metrics.get("earliest_github_repo_date", None),
                "linkedin_profile_verified": profile_metrics.get("linkedin_profile_verified", False),
                "linkedin_skill_mismatch": profile_metrics.get("linkedin_skill_mismatch", []),
                "linkedin_experience_mismatch": profile_metrics.get("linkedin_experience_mismatch", []),
                "multi_contributor_repos": int(profile_metrics.get("multi_contributor_repos", 0)),
                "engine_failed": "profile" in engine_failures,
                "failure_reason": _get_failure_reason(job_result, "profile_consistency"),
            },
            "leetcode": {
                "normalized_score": float(lc_data.get("normalized_score", 0) or 0),
                "total_solved": int(lc_metrics.get("total_solved", 0)),
                "easy": lc_easy,
                "medium": lc_medium,
                "hard": lc_hard,
                "acceptance_rate": float(lc_metrics.get("acceptance_rate", 0)),
                "ranking": int(lc_metrics.get("ranking", 0)),
                "archetype": lc_expl.get("archetype", "Unknown"),
                "engine_failed": "leetcode" in engine_failures,
                "failure_reason": _get_failure_reason(job_result, "leetcode"),
            },
            "product_mindset": {
                "normalized_score": float(pm_data.get("normalized_score", 0) or 0),
                "has_data": "product_mindset" in job_result and bool(pm_data),
                "problem_detection": pm_metrics.get("problem_ratio", 0),
                "impact_metrics": pm_metrics.get("metric_ratio", 0),
                "deployment_evidence": pm_metrics.get("deploy_ratio", 0),
                "originality": (1.0 - pm_metrics.get("tutorial_ratio", 0)) if pm_metrics else 0.0,
                "maintenance_recency": pm_metrics.get("recency_ratio", 0),
                "repos_analyzed": int(pm_metrics.get("repos_analyzed", 0)),
                "problem_hits": int(pm_metrics.get("problem_hits", 0)),
                "metric_hits": int(pm_metrics.get("metric_hits", 0)),
                "deploy_hits": int(pm_metrics.get("deploy_hits", 0)),
                "tutorial_hits": int(pm_metrics.get("tutorial_hits", 0)),
                "recent_repos": int(pm_metrics.get("recent_repos", 0)),
                "components": pm_expl.get("components", {}),
                "repo_details": pm_metrics.get("repo_details", []),
                "engine_failed": "product_mindset" in engine_failures,
                "failure_reason": _get_failure_reason(job_result, "product_mindset"),
            },
            "digital_footprint": {
                "normalized_score": float(df_data.get("normalized_score", 0) or 0),
                "has_data": "digital_footprint" in job_result and bool(df_data),
                "stackoverflow_score": float(df_expl.get("stackoverflow_pts", 0) or 0),
                "merged_pr_score": float(df_expl.get("merged_pr_pts", 0) or 0),
                "stars_score": float(df_expl.get("stars_pts", 0) or 0),
                "blog_score": float(df_expl.get("blog_pts", 0) or 0),
                "recency_score": float(df_expl.get("recency_pts", 0) or 0),
                "seo_tier": df_expl.get("seo_tier", "Unknown"),
                # Raw detail breakdowns
                "stackoverflow_detail": df_metrics.get("stackoverflow", {}),
                "merged_pr_detail": df_metrics.get("merged_prs", {}),
                "stars_detail": df_metrics.get("stars", {}),
                "blog_detail": df_metrics.get("blog", {}),
                "recency_detail": df_metrics.get("recency", {}),
                # Top repos and network reach
                "top_repos": df_metrics.get("top_repos", []),
                "followers": int(df_metrics.get("followers", 0)),
                "following": int(df_metrics.get("following", 0)),
                "total_forks": int(df_metrics.get("total_forks", 0)),
                "bio": df_metrics.get("bio"),
                "twitter_username": df_metrics.get("twitter_username"),
                "public_repos_count": int(df_metrics.get("public_repos_count", 0)),
                "engine_failed": "digital_footprint" in engine_failures,
                "failure_reason": _get_failure_reason(job_result, "digital_footprint"),
            },
            "ats_intelligence": {
                "normalized_score": float(ats_data.get("normalized_score", 0) or 0),
                "has_data": "ats_intelligence" in job_result and bool(ats_data) and not ats_data.get("engine_failed", True),
                "structure_score": float(ats_metrics.get("structure_score", 0) or 0),
                "parse_score": float(ats_metrics.get("parse_score", 0) or 0),
                "skill_authenticity_score": float(ats_metrics.get("skill_authenticity_score", 0) or 0),
                "role_alignment_score": float(ats_metrics.get("role_alignment_score", 0) or 0),
                "career_consistency_score": float(ats_metrics.get("career_consistency_score", 0) or 0),
                "keyword_stuffing_risk": ats_metrics.get("keyword_stuffing_risk", "unknown"),
                "recruiter_readability": ats_metrics.get("recruiter_readability", "Unknown"),
                "cross_validation_penalty": float(ats_metrics.get("cross_validation_penalty", 0) or 0),
                "readability_score": float(_read_d.get("readability_score", 0) or 0),
                # Structure sub-metrics (from nested structure_detail with fallback derivation)
                "section_completeness": float(_sec_comp or 0),
                "bullet_quality": float(_bq or 0),
                "metric_density": float(_struct_d.get("metric_density", 0) or 0),
                "formatting_safety": float(_fs or 0),
                # Skill sub-metrics (from nested skill_detail)
                "skill_overlap_ratio": float(_skill_d.get("overlap_ratio", 0) or 0),
                "inflation_detected": bool((_skill_d.get("inflation_ratio", 0) or 0) > 0.5),
                "buzzword_density": float(_skill_d.get("buzzword_density_pct", 0) or 0),
                # Stuffing detail
                "stuffing_detail": ats_metrics.get("stuffing_detail", {}),
                # Career detail
                "career_detail": ats_metrics.get("career_detail", {}),
                # Explanation
                "components": ats_expl,
                "warnings": ats_metrics.get("warnings", []),
                "headline": ats_expl.get("final_score", ""),
                "engine_failed": "ats_intelligence" in engine_failures,
                "failure_reason": _get_failure_reason(job_result, "ats_intelligence"),
            },
            "redflag": {
                "severity_score": float(rf_data.get("severity_score", 0) or 0),
                "risk_level": rf_flags.get("risk_level", "UNKNOWN"),
                "total_flags": rf_flags.get("total_flags", 0),
                "flags": rf_flags.get("flags", []),
                "engine_failed": "redflag" in engine_failures,
            },
        },
        "charts": {
            "commit_timeline": commit_timeline,
            "leetcode_difficulty": [
                {"label": "Easy", "value": lc_easy},
                {"label": "Medium", "value": lc_medium},
                {"label": "Hard", "value": lc_hard},
            ],
            "leetcode_trend": leetcode_trend,
        },
        "recommendation": {
            "summary": report_payload.get("recommendation", "Analysis complete."),
            "strengths": report_payload.get("strengths", []),
            "concerns": report_payload.get("concerns", []),
            "flag_details": report_payload.get("flag_details", []),
            "confidence": report_payload.get("trust_level", trust_level),
        },
    }


# ── PDF export endpoint ───────────────────────────────────
@router.get("/{job_id}/pdf")
async def export_dashboard_pdf(
    job_id: str,
    db: AsyncSession = Depends(_get_db),
) -> Response:
    """Generate a PDF report using fpdf2 (pure-Python, no system deps)."""
    from fpdf import FPDF  # type: ignore[import-untyped]

    # Re-use the dashboard aggregation logic
    dashboard_data = await get_dashboard(job_id, db)

    pdf_bytes = _render_pdf_fpdf(dashboard_data, FPDF)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="proofstack-report-{job_id[:8]}.pdf"'
        },
    )


# ── Share token endpoints ─────────────────────────────────
@router.post("/{job_id}/share")
async def create_share_link(
    job_id: str,
    db: AsyncSession = Depends(_get_db),
) -> Dict[str, Any]:
    """Create a shareable read-only link for this dashboard."""
    import secrets
    from datetime import datetime, timedelta, timezone

    # Verify the job exists
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check for an existing non-expired token
    existing_stmt = select(ShareToken).where(ShareToken.job_id == job_id)
    existing_result = await db.execute(existing_stmt)
    existing_token = existing_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if existing_token:
        if existing_token.expires_at is None or existing_token.expires_at > now:
            return {
                "token": existing_token.token,
                "share_url": f"/shared/{existing_token.token}",
                "expires_at": existing_token.expires_at.isoformat() if existing_token.expires_at else None,
            }
        # Token expired, delete it
        await db.delete(existing_token)
        await db.flush()

    # Create new token (expires in 30 days)
    token = secrets.token_urlsafe(32)
    expires = now + timedelta(days=30)
    share_token = ShareToken(token=token, job_id=job_id, expires_at=expires)
    db.add(share_token)
    await db.commit()

    return {
        "token": token,
        "share_url": f"/shared/{token}",
        "expires_at": expires.isoformat(),
    }


@public_router.get("/shared/{token}")
async def get_shared_dashboard(
    token: str,
    db: AsyncSession = Depends(_get_db),
) -> Dict[str, Any]:
    """Return dashboard data for a public share token (read-only)."""
    from datetime import datetime, timezone

    stmt = select(ShareToken).where(ShareToken.token == token)
    result = await db.execute(stmt)
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    now = datetime.now(timezone.utc)
    if share.expires_at and share.expires_at < now:
        raise HTTPException(status_code=410, detail="Share link has expired")

    # Return the dashboard data
    return await get_dashboard(share.job_id, db)


# ── Helper builders ───────────────────────────────────────
def _build_verification_items(profile_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build profile verification items for the consistency table."""
    items: List[Dict[str, Any]] = []

    skill_ratio = float(profile_metrics.get("skill_ratio", 0))
    project_ratio = float(profile_metrics.get("project_ratio", 0))
    experience_ratio = float(profile_metrics.get("experience_ratio", 0))

    skill_verified = int(profile_metrics.get("skill_verified", 0))
    skill_total = int(profile_metrics.get("skill_total", 0))
    project_verified = int(profile_metrics.get("project_verified", 0))
    project_total = int(profile_metrics.get("project_total", 0))
    exp_verified = int(profile_metrics.get("experience_verified", 0))
    exp_total = int(profile_metrics.get("experience_total", 0))

    items.append({
        "data_point": "Technical Skills",
        "source_a": f"{skill_total} claimed",
        "source_b": f"{skill_verified} verified in repos",
        "confidence": round(skill_ratio * 100),
    })
    items.append({
        "data_point": "Projects",
        "source_a": f"{project_total} listed",
        "source_b": f"{project_verified} found on GitHub",
        "confidence": round(project_ratio * 100),
    })
    items.append({
        "data_point": "Experience Timeline",
        "source_a": f"{exp_total} positions claimed",
        "source_b": f"{exp_verified} corroborated",
        "confidence": round(experience_ratio * 100),
    })

    # LinkedIn verification if available
    linkedin_verified = profile_metrics.get("linkedin_profile_verified", False)
    if linkedin_verified:
        items.append({
            "data_point": "LinkedIn Profile",
            "source_a": "Resume data",
            "source_b": "LinkedIn API verified",
            "confidence": 100,
        })

    return items


def _build_commit_timeline(gh_metrics: Dict[str, Any], gh_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Build commit timeline from GitHub metrics (monthly aggregation).

    Priority:
      1. Real monthly_commits from engine (actual commit dates → YYYY-MM buckets)
      2. Real per-repo commit counts (repo_details from engine)
      3. Estimated distribution (clearly labeled, deterministic, no randomness)
    """
    # Priority 1: Real monthly data from engine
    timeline = gh_metrics.get("monthly_commits", [])
    if timeline and isinstance(timeline, list):
        return [{"date": p.get("date", ""), "count": p.get("count", 0), "source": "real"} for p in timeline]

    # Priority 2: Per-repo commit counts (real data, different axis)
    repo_details = gh_metrics.get("repo_details", [])
    if repo_details and isinstance(repo_details, list):
        points = []
        for repo in repo_details[:12]:
            name = repo.get("name", "repo")
            commits = repo.get("commits", 0)
            points.append({"date": name, "count": commits, "source": "per_repo"})
        return points

    # Priority 3: Honest estimated distribution (no random — uses even split)
    total_commits = int(gh_metrics.get("total_commits", 0))
    total_repos = int(gh_metrics.get("total_repositories", 0))
    avg_age = float(gh_metrics.get("average_repo_age_days", 0))
    if total_commits > 0 and total_repos > 0:
        months = max(1, min(12, int(avg_age / 30)))
        avg_per_month = total_commits / months
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        burst = bool(gh_metrics.get("burst_flag", False))
        points = []
        for i in range(months):
            # Deterministic distribution: even split with slight ramp
            # No randomness — uses position-based weighting
            weight = 0.7 + (i / max(months - 1, 1)) * 0.6 if not burst else (
                0.2 if i < months - 2 else 3.0
            )
            count = max(1, int(avg_per_month * weight))
            label = month_labels[i % 12]
            points.append({"date": label, "count": count, "source": "estimated"})
        # Normalize to match total
        current_total = sum(p["count"] for p in points)
        if current_total > 0:
            scale = total_commits / current_total
            for p in points:
                p["count"] = max(1, int(p["count"] * scale))
        return points

    return []


def _build_leetcode_trend(lc_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build monthly LeetCode trend."""
    trend = lc_metrics.get("monthly_trend", [])
    if trend and isinstance(trend, list):
        return [{"month": p.get("month", ""), "submissions": p.get("submissions", 0)} for p in trend]

    # Synthesize from recent_in_90d if available
    recent = int(lc_metrics.get("recent_in_90d", 0))
    total = int(lc_metrics.get("total_solved", 0))
    if total > 0:
        # Approximate monthly progression
        monthly_avg = max(1, recent // 3)
        months = ["6mo ago", "5mo ago", "4mo ago", "3mo ago", "2mo ago", "Last mo"]
        return [
            {"month": m, "submissions": max(1, int(monthly_avg * (0.5 + i * 0.15)))}
            for i, m in enumerate(months)
        ]

    return []


def _get_failure_reason(job_result: Dict[str, Any], engine_name: str) -> Optional[str]:
    """Extract failure reason from the job result for a specific engine."""
    engine_data = job_result.get(engine_name, {})
    if isinstance(engine_data, dict):
        return engine_data.get("failure_reason")
    return None


def _get_rate_limited(job_result: Dict[str, Any], engine_name: str) -> bool:
    """Check if an engine was rate-limited."""
    engine_data = job_result.get(engine_name, {})
    if isinstance(engine_data, dict):
        return engine_data.get("rate_limited", False)
    return False


# ── PDF renderer (fpdf2) ───────────────────────────────────
def _render_pdf_fpdf(data: Dict[str, Any], FPDF) -> bytes:
    """Render a comprehensive, professionally formatted PDF report using fpdf2."""

    username = data.get("username", "Unknown")
    role_level = data.get("role_level", "mid")
    trust_score = data.get("trust_score", 0)
    trust_band = data.get("trust_band", "No Data")
    engines = data.get("engines", {})
    rec = data.get("recommendation", {})
    escalation = data.get("escalation", {})
    pst_components = data.get("pst_components", {})

    # ── Colour palette ──
    BLUE = (26, 115, 232)
    DARK = (32, 33, 36)
    GREY = (95, 99, 104)
    LIGHT_BG = (248, 249, 250)
    GREEN = (30, 142, 62)
    RED = (217, 48, 37)
    AMBER = (249, 171, 0)
    WHITE = (255, 255, 255)
    BLUE_LIGHT = (232, 240, 254)

    # Unicode → ASCII replacements for Helvetica compatibility
    _UNICODE_MAP = str.maketrans({
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "*",
        "\u00e9": "e", "\u00e8": "e", "\u00f1": "n", "\u00fc": "u",
        "\u2192": "->", "\u2190": "<-", "\u2713": "[ok]", "\u2717": "[x]",
        "\u00a0": " ", "\u200b": "",
    })

    def _sanitize(text) -> str:
        """Strip non-latin1 chars so Helvetica doesn't choke."""
        s = str(text).translate(_UNICODE_MAP)
        return s.encode("latin-1", errors="replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Helper functions ──
    def _color(rgb):
        pdf.set_text_color(*rgb)

    def _fill(rgb):
        pdf.set_fill_color(*rgb)

    def _safe_multi(text: str, h: float = 5, indent: float = 0):
        """multi_cell wrapper that resets X to avoid right-edge bugs."""
        pdf.set_x(pdf.l_margin + indent)
        w = pdf.w - pdf.l_margin - pdf.r_margin - indent
        pdf.multi_cell(w, h, _sanitize(text))

    def _section_title(title: str, icon_char: str = ""):
        """Add a section heading with blue accent bar."""
        pdf.ln(6)
        _fill(BLUE)
        pdf.rect(10, pdf.get_y(), 3, 8, "F")
        pdf.set_x(16)
        _color(DARK)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*BLUE_LIGHT)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

    def _kv_row(label: str, value: str, bold_value: bool = False):
        """Print a label: value row."""
        pdf.set_font("Helvetica", "", 9)
        _color(GREY)
        pdf.cell(55, 6, _sanitize(label))
        _color(DARK)
        pdf.set_font("Helvetica", "B" if bold_value else "", 9)
        pdf.cell(0, 6, _sanitize(value), new_x="LMARGIN", new_y="NEXT")

    def _metric_bar(label: str, value: float, max_val: float = 100, suffix: str = "", reverse: bool = False):
        """Draw a metric with label, bar, value."""
        pdf.set_font("Helvetica", "", 9)
        _color(DARK)
        pdf.cell(55, 7, label)

        bar_x = pdf.get_x() + 2
        bar_y = pdf.get_y() + 2.5
        bar_w = 70
        bar_h = 3

        _fill(BLUE_LIGHT)
        pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")

        pct = max(0, min(1, value / max_val)) if max_val > 0 else 0
        fill_w = bar_w * pct
        if reverse:
            c = RED if pct > 0.5 else GREEN
        else:
            c = GREEN if pct >= 0.7 else AMBER if pct >= 0.4 else RED
        _fill(c)
        if fill_w > 0:
            pdf.rect(bar_x, bar_y, fill_w, bar_h, "F")

        pdf.set_x(bar_x + bar_w + 3)
        pdf.set_font("Helvetica", "B", 9)
        display = f"{value:.1f}{suffix}" if isinstance(value, float) else f"{value}{suffix}"
        pdf.cell(0, 7, display, new_x="LMARGIN", new_y="NEXT")

    def _warning_list(warnings):
        """Print a list of warnings."""
        if not warnings:
            return
        pdf.set_font("Helvetica", "", 8)
        for w in warnings[:8]:
            msg = w.get("message", w) if isinstance(w, dict) else str(w)
            _color(AMBER)
            pdf.cell(5)
            pdf.cell(5, 5, "!")
            _color(GREY)
            pdf.cell(0, 5, _sanitize(msg[:100]), new_x="LMARGIN", new_y="NEXT")

    def _check_page_space(needed: int = 50):
        """Add page if less than needed mm remain."""
        if pdf.get_y() > 297 - needed:
            pdf.add_page()

    # ═══════════════════════════════════════════════════════
    # PAGE 1 — Cover / Trust Score / Engine Overview
    # ═══════════════════════════════════════════════════════
    pdf.add_page()

    # ── Header banner ──
    _fill(BLUE)
    pdf.rect(0, 0, 210, 42, "F")
    _color(WHITE)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_y(8)
    pdf.cell(0, 12, "ProofStack Intelligence Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _sanitize(f"Candidate: {username}  |  Role Level: {role_level.title()}"), align="C", new_x="LMARGIN", new_y="NEXT")
    from datetime import datetime
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", align="C", new_x="LMARGIN", new_y="NEXT")
    _color(DARK)

    # ── Trust Score hero ──
    pdf.ln(8)
    cx = 105
    cy = pdf.get_y() + 20
    _fill(BLUE_LIGHT)
    pdf.ellipse(cx - 20, cy - 20, 40, 40, "F")
    pdf.set_font("Helvetica", "B", 32)
    _color(BLUE)
    pdf.set_xy(cx - 20, cy - 11)
    pdf.cell(40, 22, f"{trust_score:.0f}", align="C")
    _color(DARK)
    pdf.set_y(cy + 24)

    # Trust band
    band_color = GREEN if trust_score >= 70 else AMBER if trust_score >= 40 else RED
    pdf.set_font("Helvetica", "B", 11)
    _color(band_color)
    pdf.cell(0, 7, f"Trust Level: {trust_band.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
    _color(DARK)

    # PST component scores
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 8)
    _color(GREY)
    comps = []
    for k, label in [("github_score", "GitHub"), ("profile_score", "Profile"), ("leetcode_score", "LeetCode"), ("ats_score", "ATS"), ("redflag_severity", "RedFlag")]:
        v = pst_components.get(k, 0)
        comps.append(f"{label}: {v:.0f}")
    pdf.cell(0, 5, "   |   ".join(comps), align="C", new_x="LMARGIN", new_y="NEXT")
    _color(DARK)

    # ── Escalation ──
    esc_reasons = escalation.get("escalation_reasons", [])
    if esc_reasons:
        pdf.ln(4)
        _fill((254, 242, 242))
        y0 = pdf.get_y()
        pdf.set_font("Helvetica", "B", 9)
        _color(RED)
        pdf.cell(0, 6, "  ESCALATION APPLIED", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for r in esc_reasons:
            pdf.cell(8)
            pdf.cell(0, 5, _sanitize(f"- {r}"), new_x="LMARGIN", new_y="NEXT")
        y1 = pdf.get_y() + 2
        pdf.set_draw_color(254, 202, 202)
        pdf.rect(10, y0 - 1, 190, y1 - y0 + 2, "D")
        pdf.set_y(y1 + 2)
        _color(DARK)

    # ── Engine Overview Table ──
    _section_title("Engine Score Overview")

    engine_rows = [
        ("GitHub Authenticity", engines.get("github", {}).get("normalized_score", 0)),
        ("Profile Consistency", engines.get("profile", {}).get("normalized_score", 0)),
        ("Problem Solving (LeetCode)", engines.get("leetcode", {}).get("normalized_score", 0)),
        ("Product Mindset", engines.get("product_mindset", {}).get("normalized_score", 0)),
        ("Digital Footprint", engines.get("digital_footprint", {}).get("normalized_score", 0)),
        ("ATS Resume Intelligence", engines.get("ats_intelligence", {}).get("normalized_score", 0)),
    ]
    rf_sev = engines.get("redflag", {}).get("severity_score", 0)

    # Table header
    _fill(LIGHT_BG)
    pdf.set_font("Helvetica", "B", 8)
    _color(GREY)
    pdf.cell(70, 7, "ENGINE", border="B", fill=True)
    pdf.cell(25, 7, "SCORE", border="B", fill=True, align="C")
    pdf.cell(95, 7, "", border="B", fill=True, new_x="LMARGIN", new_y="NEXT")

    for name, score in engine_rows:
        _color(DARK)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(70, 8, name, border="B")
        color = GREEN if score >= 70 else AMBER if score >= 40 else RED
        _color(color)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(25, 8, f"{score:.1f}", border="B", align="C")

        # Progress bar
        bx = pdf.get_x() + 2
        by = pdf.get_y() + 3
        _fill(BLUE_LIGHT)
        pdf.rect(bx, by, 85, 3, "F")
        _fill(color)
        fw = max(0, min(85, 85 * score / 100))
        if fw > 0:
            pdf.rect(bx, by, fw, 3, "F")

        pdf.cell(95, 8, "", border="B", new_x="LMARGIN", new_y="NEXT")

    # Red Flag row (reversed colors)
    _color(DARK)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(70, 8, "Red Flag Severity", border="B")
    rf_color = RED if rf_sev > 30 else AMBER if rf_sev > 10 else GREEN
    _color(rf_color)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 8, f"{rf_sev:.1f}", border="B", align="C")
    bx = pdf.get_x() + 2
    by = pdf.get_y() + 3
    _fill(BLUE_LIGHT)
    pdf.rect(bx, by, 85, 3, "F")
    _fill(rf_color)
    fw = max(0, min(85, 85 * rf_sev / 100))
    if fw > 0:
        pdf.rect(bx, by, fw, 3, "F")
    pdf.cell(95, 8, "", border="B", new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════
    # PAGE 2+ — Detailed Engine Analysis
    # ═══════════════════════════════════════════════════════
    pdf.add_page()

    # ── 1. GitHub Authenticity ──
    gh = engines.get("github", {})
    _section_title("1. GitHub Authenticity")
    _metric_bar("Overall Score", gh.get("normalized_score", 0), suffix="/100")
    _kv_row("Total Commits", str(gh.get("commit_count", 0)))
    _kv_row("Repositories Analyzed", str(gh.get("repo_count", 0)))
    _kv_row("Commit Entropy", f"{gh.get('entropy', 0):.2f} ({gh.get('entropy_label', 'N/A')})")
    _kv_row("Structural Consistency", f"{gh.get('consistency', 0):.2f}")
    _kv_row("Avg Branches per Repo", f"{gh.get('avg_branches', 0):.1f}")
    _kv_row("Avg Contributors", f"{gh.get('avg_contributors', 0):.1f}")
    _kv_row("Avg Repo Age", f"{gh.get('avg_repo_age_days', 0):.0f} days")
    _kv_row("Burst Pattern Detected", "Yes" if gh.get("burst_detected") else "No", bold_value=True)

    # ── 2. Advanced GitHub ──
    adv = engines.get("advanced_github", {})
    _check_page_space(55)
    _section_title("2. Advanced GitHub Analysis")
    _metric_bar("Anomaly Score", adv.get("anomaly_score", 0), suffix="/100", reverse=True)
    _kv_row("LOC Anomaly Ratio", f"{adv.get('loc_anomaly_ratio', 0):.3f}")
    _kv_row("Commit Interval CV", f"{adv.get('interval_cv', 0):.2f}")
    _kv_row("Empty Commit Ratio", f"{adv.get('empty_commit_ratio', 0):.3f}")
    _kv_row("Repetitive Message Ratio", f"{adv.get('repetitive_message_ratio', 0):.3f}")
    _kv_row("Commits Inspected", str(adv.get("total_commits_inspected", 0)))

    # ── 3. Profile Consistency ──
    prof = engines.get("profile", {})
    _check_page_space(70)
    _section_title("3. Profile Consistency")
    _metric_bar("Overall Score", prof.get("normalized_score", 0), suffix="/100")

    # Verification table
    verification = prof.get("verification_items", [])
    if verification:
        pdf.ln(2)
        _fill(LIGHT_BG)
        pdf.set_font("Helvetica", "B", 8)
        _color(GREY)
        pdf.cell(45, 6, "DATA POINT", border="B", fill=True)
        pdf.cell(45, 6, "SOURCE A (RESUME)", border="B", fill=True)
        pdf.cell(50, 6, "SOURCE B (DIGITAL)", border="B", fill=True)
        pdf.cell(25, 6, "CONFIDENCE", border="B", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

        for item in verification:
            _color(DARK)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(45, 6, _sanitize(item.get("data_point", "")), border="B")
            pdf.cell(45, 6, _sanitize(item.get("source_a", "")), border="B")
            pdf.cell(50, 6, _sanitize(item.get("source_b", "")), border="B")
            conf = item.get("confidence", 0)
            conf_color = GREEN if conf >= 70 else AMBER if conf >= 40 else RED
            _color(conf_color)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(25, 6, f"{conf}%", border="B", align="C", new_x="LMARGIN", new_y="NEXT")

    # Mismatch details
    skill_mm = prof.get("skill_mismatches", [])
    if skill_mm:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 8)
        _color(AMBER)
        pdf.cell(0, 5, f"Unverified Skills ({len(skill_mm)}):", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        _color(GREY)
        pdf.cell(5)
        pdf.cell(0, 5, _sanitize(", ".join(str(s) for s in skill_mm[:15])), new_x="LMARGIN", new_y="NEXT")

    # ── 4. Problem Solving (LeetCode) ──
    lc = engines.get("leetcode", {})
    _check_page_space(60)
    _section_title("4. Problem Solving (LeetCode)")
    _metric_bar("Overall Score", lc.get("normalized_score", 0), suffix="/100")
    _kv_row("Total Problems Solved", str(lc.get("total_solved", 0)))
    _kv_row("Archetype", str(lc.get("archetype", "Unknown")), bold_value=True)
    _kv_row("Acceptance Rate", f"{lc.get('acceptance_rate', 0):.1f}%")
    _kv_row("Global Ranking", str(lc.get("ranking", 0) or "N/A"))

    # Difficulty breakdown
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    _color(DARK)
    pdf.cell(0, 6, "Difficulty Breakdown:", new_x="LMARGIN", new_y="NEXT")

    easy = lc.get("easy", 0)
    med = lc.get("medium", 0)
    hard = lc.get("hard", 0)
    total_solved = max(easy + med + hard, 1)

    for label, val, clr in [("Easy", easy, GREEN), ("Medium", med, AMBER), ("Hard", hard, RED)]:
        pdf.set_font("Helvetica", "", 8)
        _color(DARK)
        pdf.cell(20, 6, label)
        bx = pdf.get_x()
        by = pdf.get_y() + 2
        _fill(BLUE_LIGHT)
        pdf.rect(bx, by, 80, 3, "F")
        _fill(clr)
        fw = 80 * val / total_solved if total_solved > 0 else 0
        if fw > 0:
            pdf.rect(bx, by, fw, 3, "F")
        pdf.set_x(bx + 83)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 6, str(val), new_x="LMARGIN", new_y="NEXT")

    # ── 5. Product Mindset ──
    pm = engines.get("product_mindset", {})
    _check_page_space(65)
    _section_title("5. Product Mindset")
    _metric_bar("Overall Score", pm.get("normalized_score", 0), suffix="/100")
    _kv_row("Repos Analyzed", str(pm.get("repos_analyzed", 0)))

    pdf.ln(2)
    pm_metrics_list = [
        ("Problem Detection", pm.get("problem_detection", 0)),
        ("Impact Metrics", pm.get("impact_metrics", 0)),
        ("Deployment Evidence", pm.get("deployment_evidence", 0)),
        ("Originality Index", pm.get("originality", 0)),
        ("Maintenance Recency", pm.get("maintenance_recency", 0)),
    ]
    for label, val in pm_metrics_list:
        _metric_bar(label, val * 100 if val <= 1 else val, suffix="%")

    pdf.ln(1)
    _kv_row("Problem Hits", str(pm.get("problem_hits", 0)))
    _kv_row("Metric Hits", str(pm.get("metric_hits", 0)))
    _kv_row("Deploy Evidence Hits", str(pm.get("deploy_hits", 0)))
    _kv_row("Tutorial Matches", str(pm.get("tutorial_hits", 0)))
    _kv_row("Recent Active Repos", str(pm.get("recent_repos", 0)))

    # ── 6. Digital Footprint ──
    df = engines.get("digital_footprint", {})
    _check_page_space(65)
    _section_title("6. Digital Footprint")
    _metric_bar("Overall Score", df.get("normalized_score", 0), suffix="/100")
    _kv_row("SEO Tier", str(df.get("seo_tier", "Unknown")), bold_value=True)

    pdf.ln(2)
    df_subs = [
        ("Stack Overflow", df.get("stackoverflow_score", 0)),
        ("Merged Pull Requests", df.get("merged_pr_score", 0)),
        ("GitHub Stars", df.get("stars_score", 0)),
        ("Blog / Writing", df.get("blog_score", 0)),
        ("Recency", df.get("recency_score", 0)),
    ]
    for label, val in df_subs:
        _metric_bar(label, val, max_val=30, suffix=" pts")

    pdf.ln(1)
    _kv_row("Followers", str(df.get("followers", 0)))
    _kv_row("Following", str(df.get("following", 0)))
    _kv_row("Total Forks", str(df.get("total_forks", 0)))
    _kv_row("Public Repos", str(df.get("public_repos_count", 0)))
    if df.get("bio"):
        _kv_row("Bio", str(df["bio"])[:80])

    # ── 7. ATS Resume Intelligence ──
    ats = engines.get("ats_intelligence", {})
    _check_page_space(90)
    _section_title("7. ATS Resume Intelligence")
    _metric_bar("Overall Score", ats.get("normalized_score", 0), suffix="/100")
    _kv_row("Keyword Stuffing Risk", str(ats.get("keyword_stuffing_risk", "unknown")).title(), bold_value=True)
    _kv_row("Recruiter Readability", str(ats.get("recruiter_readability", "Unknown")), bold_value=True)
    if ats.get("cross_validation_penalty", 0) > 0:
        _kv_row("Cross-Validation Penalty", f"-{ats['cross_validation_penalty']:.1f} pts")

    # Score breakdown
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    _color(DARK)
    pdf.cell(0, 6, "Score Breakdown:", new_x="LMARGIN", new_y="NEXT")

    ats_subs = [
        ("Structure Quality", ats.get("structure_score", 0)),
        ("Skill Authenticity", ats.get("skill_authenticity_score", 0)),
        ("Role Alignment", ats.get("role_alignment_score", 0)),
        ("Career Consistency", ats.get("career_consistency_score", 0)),
        ("Parse Quality", ats.get("parse_score", 0)),
        ("Readability", ats.get("readability_score", 0)),
    ]
    for label, val in ats_subs:
        _metric_bar(label, val, suffix="/100")

    # Structure sub-metrics
    _check_page_space(40)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    _color(DARK)
    pdf.cell(0, 6, "Structure Analysis:", new_x="LMARGIN", new_y="NEXT")

    struct_items = [
        ("Section Completeness", ats.get("section_completeness", 0) * 100),
        ("Bullet Quality", ats.get("bullet_quality", 0) * 100),
        ("Metric Density", ats.get("metric_density", 0) * 100),
        ("Formatting Safety", ats.get("formatting_safety", 0) * 100),
    ]
    for label, val in struct_items:
        _metric_bar(label, val, suffix="%")

    # Skill authentication
    pdf.ln(1)
    _kv_row("Skill Overlap Ratio", f"{ats.get('skill_overlap_ratio', 0) * 100:.0f}%")
    _kv_row("Inflation Detected", "Yes" if ats.get("inflation_detected") else "No")
    _kv_row("Buzzword Density", f"{ats.get('buzzword_density', 0):.2f}%")

    # Career detail
    career = ats.get("career_detail", {})
    if career:
        pdf.ln(1)
        _kv_row("Career Gaps", f"{career.get('gap_months', 0)} months")
        _kv_row("Overlapping Roles", str(career.get("overlaps", 0)))
        _kv_row("Avg Tenure", f"{career.get('avg_tenure_months', 0):.0f} months")

    # ATS Warnings
    ats_warnings = ats.get("warnings", [])
    if ats_warnings:
        _check_page_space(30)
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 8)
        _color(AMBER)
        pdf.cell(0, 5, "ATS Warnings:", new_x="LMARGIN", new_y="NEXT")
        _warning_list(ats_warnings)

    # ── 8. Red Flags ──
    rf = engines.get("redflag", {})
    _check_page_space(50)
    _section_title("8. Red Flag Analysis")
    severity = rf.get("severity_score", 0)
    _metric_bar("Severity Score", severity, suffix="/100", reverse=True)
    _kv_row("Risk Level", str(rf.get("risk_level", "UNKNOWN")).upper(), bold_value=True)
    _kv_row("Total Flags", str(rf.get("total_flags", 0)))

    flags = rf.get("flags", [])
    if flags:
        pdf.ln(2)
        _fill(LIGHT_BG)
        pdf.set_font("Helvetica", "B", 8)
        _color(GREY)
        pdf.cell(55, 6, "FLAG", border="B", fill=True)
        pdf.cell(20, 6, "SEVERITY", border="B", fill=True, align="C")
        pdf.cell(100, 6, "DETAIL", border="B", fill=True, new_x="LMARGIN", new_y="NEXT")

        for flag in flags[:15]:
            _check_page_space(10)
            _color(DARK)
            pdf.set_font("Helvetica", "", 8)
            flag_name = flag.get("flag", flag.get("name", "Unknown"))[:30]
            sev = flag.get("severity", "LOW")
            detail = flag.get("detail", flag.get("message", ""))[:55]

            pdf.cell(55, 6, _sanitize(flag_name), border="B")
            sev_color = RED if sev == "HIGH" else AMBER if sev == "MEDIUM" else GREEN
            _color(sev_color)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(20, 6, str(sev), border="B", align="C")
            _color(GREY)
            pdf.set_font("Helvetica", "", 7)
            pdf.cell(100, 6, _sanitize(detail), border="B", new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════
    # RECOMMENDATION SECTION
    # ═══════════════════════════════════════════════════════
    _check_page_space(60)
    _section_title("Recommendation & Summary")

    summary = rec.get("summary", "Analysis complete.")
    pdf.set_font("Helvetica", "", 9)
    _color(DARK)
    _safe_multi(summary)

    strengths = rec.get("strengths", [])
    if strengths:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        _color(GREEN)
        pdf.cell(0, 6, "Strengths", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        _color(DARK)
        for s in strengths:
            _check_page_space(8)
            _safe_multi(f"+ {s}", indent=5)

    concerns = rec.get("concerns", [])
    if concerns:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        _color(RED)
        pdf.cell(0, 6, "Concerns", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        _color(DARK)
        for c in concerns:
            _check_page_space(8)
            _safe_multi(f"- {c}", indent=5)

    flag_details = rec.get("flag_details", [])
    if flag_details:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        _color(AMBER)
        pdf.cell(0, 6, "Flag Details", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        _color(DARK)
        for fd in flag_details:
            _check_page_space(8)
            _safe_multi(f"- {fd}", indent=5)

    # ═══════════════════════════════════════════════════════
    # FOOTER on every page
    # ═══════════════════════════════════════════════════════
    for page_num in range(1, pdf.pages_count + 1):
        pdf.page = page_num
        pdf.set_y(-15)
        pdf.set_draw_color(218, 220, 224)
        pdf.line(10, 287, 200, 287)
        pdf.set_font("Helvetica", "I", 7)
        _color(GREY)
        pdf.cell(95, 5, f"ProofStack Intelligence  |  Confidential", align="L")
        pdf.cell(95, 5, f"Page {page_num} of {pdf.pages_count}", align="R")

    return bytes(pdf.output())
