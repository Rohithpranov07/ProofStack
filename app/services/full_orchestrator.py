"""Unified Full Analysis Orchestrator.

Runs all engines with shared GitHub data, explicit error handling,
advanced anomaly integration, run_id-based result isolation,
per-engine timeout enforcement, exponential retry for external APIs,
structured observability logging with per-engine timing, and
rate-limit propagation.

Execution order:
  0. Fetch GitHub repos ONCE (shared across engines, with retry)
  1. GitHub Authenticity Engine      -> GitHubAnalysis row
  1b. Advanced GitHub Anomaly Engine -> AdvancedGitHubAnalysis row
  2. Profile Consistency Engine      -> ProfileConsistency row
  3. LeetCode Pattern Engine         -> LeetCodeAnalysis row  (with retry)
  4. Red Flag Detection Engine       -> RedFlagAnalysis row
  5. Product Mindset Engine          -> ProductMindsetAnalysis row
  6. Digital Footprint Engine        -> DigitalFootprintAnalysis row  (with retry)
  7. PST Aggregation Engine          -> PSTReport row
  8. Recruiter Report                -> RecruiterReport row

Every engine call is wrapped in ``asyncio.wait_for(…, timeout=ENGINE_TIMEOUT)``.
External-API engines (GitHub fetch, LeetCode, DigitalFootprint) get exponential retry (max 3).
Every engine produces a structured result with ``engine_failed`` / ``failure_reason``
fields.  Rate-limited calls set ``rate_limited: True``.
All results for a single run share the same ``run_id``.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import TimerContext, logger, structured_log
from app.db.models import (
    AdvancedGitHubAnalysis,
    ATSResumeAnalysis,
    GitHubAnalysis,
    LeetCodeAnalysis,
    ProductMindsetAnalysis,
    ProfileConsistency,
    PSTReport,
    RecruiterReport,
    RedFlagAnalysis,
    UserConsent,
)
from app.schemas.profile import LinkedInStructured, ResumeStructured
from app.services.advanced_github_engine import AdvancedGitHubEngine
from app.services.ats_engine import ATSIntelligenceEngine
from app.services.github_auth_engine import GitHubAuthenticityEngine
from app.services.github_client import GitHubClient
from app.services.leetcode_engine import LeetCodeEngine
from app.services.product_mindset_engine import ProductMindsetEngine
from app.services.profile_consistency_engine import ProfileConsistencyEngine
from app.services.pst_engine import PSTAggregationEngine
from app.services.redflag_engine import RedFlagEngine
from app.services.report_engine import RecruiterReportEngine

# ── try importing optional engines / models ───────────────
try:
    from app.services.digital_footprint_engine import DigitalFootprintEngine  # type: ignore[import-untyped]
    from app.db.models import DigitalFootprintAnalysis  # type: ignore[attr-defined]
    _HAS_DIGITAL_FOOTPRINT = True
except ImportError:
    _HAS_DIGITAL_FOOTPRINT = False

# ── constants ─────────────────────────────────────────────
ENGINE_TIMEOUT: float = 60.0  # seconds per engine call
API_MAX_RETRIES: int = 3
API_RETRY_BASE: float = 1.0   # exponential back-off base (seconds)


async def _with_timeout(coro, label: str, timeout: float = ENGINE_TIMEOUT):
    """Run *coro* with a hard timeout; raise on expiry."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError(f"{label} timed out after {timeout}s")


async def _retry_async(coro_factory, label: str, max_retries: int = API_MAX_RETRIES):
    """Retry *coro_factory()* with exponential back-off.

    ``coro_factory`` is a zero-arg callable that returns a fresh coroutine
    each time (you can't re-await the same coroutine).

    Returns ``(result, retry_count)`` where *retry_count* is the number
    of retries actually performed (0 = first attempt succeeded).
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            result = await _with_timeout(coro_factory(), label)
            return result, attempt - 1
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = API_RETRY_BASE * (2 ** (attempt - 1))
                structured_log(
                    "engine_retry",
                    level="warning",
                    label=label,
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(exc),
                    next_delay_s=delay,
                )
                await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


def _is_rate_limited(exc: BaseException) -> bool:
    """Return True if the exception signals an API rate-limit."""
    # GitHubRateLimitError is raised by github_client
    name = type(exc).__name__
    if "RateLimit" in name:
        return True
    msg = str(exc).lower()
    return "rate limit" in msg or "429" in msg or "403" in msg


def _engine_default(
    *,
    score_key: str = "normalized_score",
    score_val: float = 0.0,
) -> Dict[str, Any]:
    """Return a safe default engine result dict (structured contract)."""
    return {
        "raw_metrics": {},
        score_key: score_val,
        "explanation": {},
        "engine_failed": True,
        "failure_reason": None,
        "rate_limited": False,
    }


class FullAnalysisOrchestrator:
    """Orchestrates a complete analysis pipeline for a single candidate."""

    def __init__(self) -> None:
        self.github_client = GitHubClient()
        self.github_engine = GitHubAuthenticityEngine()
        self.advanced_engine = AdvancedGitHubEngine()
        self.profile_engine = ProfileConsistencyEngine()
        self.leetcode_engine = LeetCodeEngine()
        self.redflag_engine = RedFlagEngine()
        self.mindset_engine = ProductMindsetEngine()
        self.digital_engine = DigitalFootprintEngine() if _HAS_DIGITAL_FOOTPRINT else None
        self.ats_engine = ATSIntelligenceEngine()
        self.pst_engine = PSTAggregationEngine()
        self.report_engine = RecruiterReportEngine()

    # ── public entry-point ────────────────────────────────────

    async def run_full_analysis(
        self,
        username: str,
        role_level: str,
        resume_data: ResumeStructured,
        linkedin_data: Optional[LinkedInStructured],
        leetcode_username: Optional[str],
        db: AsyncSession,
        *,
        resume_text: Optional[str] = None,
        analysis_version: int = 1,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the full pipeline with shared data and error handling."""
        self._job_id = job_id  # stored for Gate 3 consent check
        run_id = str(uuid.uuid4())
        logger.info(f"[{run_id}] Starting full analysis pipeline for {username}")
        structured_log("pipeline_start", run_id=run_id, username=username, role_level=role_level, analysis_version=analysis_version)

        engine_failures: List[str] = []

        # ── Step 0: Fetch GitHub repos ONCE (with retry) ─────
        repos_timer = TimerContext()
        retry_count_repos = 0
        try:
            with repos_timer:
                repos, retry_count_repos = await _retry_async(
                    lambda: self.github_client.get_repos(username),
                    label=f"[{run_id}] GitHub repo fetch",
                )
            structured_log("repo_fetch_complete", run_id=run_id, duration_ms=repos_timer.elapsed_ms, retry_count=retry_count_repos)
        except Exception as exc:
            logger.exception(f"[{run_id}] Failed to fetch GitHub repos for {username} after retries")
            structured_log("repo_fetch_failed", level="error", run_id=run_id, error=str(exc), rate_limited=_is_rate_limited(exc))
            repos = []

        # ── Structured defaults (contract: every result carries engine_failed/failure_reason/rate_limited) ─

        github_result: Dict[str, Any] = _engine_default()
        advanced_result: Dict[str, Any] = _engine_default(score_key="anomaly_score")
        profile_result: Dict[str, Any] = _engine_default()
        leetcode_result: Dict[str, Any] = _engine_default()
        mindset_result: Dict[str, Any] = _engine_default()
        digital_result: Dict[str, Any] = _engine_default()
        ats_result: Dict[str, Any] = _engine_default()

        # ── Prepare engine coroutine factories ───────────────

        async def _run_github() -> Dict[str, Any]:
            return await _with_timeout(
                self.github_engine.analyze(username, repos=repos),
                f"[{run_id}] Engine 1 (GitHub)",
            )

        async def _run_advanced() -> Dict[str, Any]:
            return await _with_timeout(
                self.advanced_engine.analyze(username, repos=repos),
                f"[{run_id}] Engine 1b (Advanced)",
            )

        async def _run_profile() -> Dict[str, Any]:
            return await _with_timeout(
                self.profile_engine.analyze(username, resume_data, linkedin_data, repos=repos),
                f"[{run_id}] Engine 2 (Profile)",
            )

        async def _run_leetcode() -> Optional[Dict[str, Any]]:
            if not leetcode_username:
                return None
            result, _ = await _retry_async(
                lambda: self.leetcode_engine.analyze(leetcode_username),
                label=f"[{run_id}] Engine 3 (LeetCode)",
            )
            return result

        async def _run_mindset() -> Dict[str, Any]:
            return await _with_timeout(
                self.mindset_engine.analyze(username, repos=repos),
                f"[{run_id}] Engine 5 (ProductMindset)",
            )

        async def _run_digital() -> Optional[Dict[str, Any]]:
            if not self.digital_engine:
                return None
            result, _ = await _retry_async(
                lambda: self.digital_engine.analyze(username, repos=repos),
                label=f"[{run_id}] Engine 6 (DigitalFootprint)",
            )
            return result

        async def _run_ats() -> Optional[Dict[str, Any]]:
            if not resume_text:
                return None
            # Extract GitHub languages from repos
            gh_langs = list({
                r.get("language", "")
                for r in repos if r.get("language")
            })
            gh_commits = sum(r.get("commits", 0) for r in repos)
            return await _with_timeout(
                self.ats_engine.analyze(
                    username,
                    resume_text,
                    role_level=role_level,
                    github_languages=gh_langs,
                    github_repos=repos,
                    github_total_commits=gh_commits,
                ),
                f"[{run_id}] Engine 8 (ATS)",
            )

        # Fire all engines at once
        engine_timer = TimerContext()
        with engine_timer:
            tasks = [
                _run_github(), _run_advanced(), _run_profile(),
                _run_leetcode(), _run_mindset(), _run_digital(),
                _run_ats(),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        structured_log("parallel_engines_done", run_id=run_id, duration_ms=engine_timer.elapsed_ms)

        # ── helper to stamp structured fields on a good result ─
        def _stamp_ok(result_dict: Dict[str, Any]) -> Dict[str, Any]:
            result_dict.setdefault("engine_failed", False)
            result_dict.setdefault("failure_reason", None)
            result_dict.setdefault("rate_limited", False)
            return result_dict

        # ── Process Engine 1: GitHub ──────────────────────────
        if isinstance(results[0], Exception):
            logger.exception(f"[{run_id}] Engine 1 (GitHub) FAILED for {username}: {results[0]}")
            github_result["failure_reason"] = str(results[0])
            github_result["rate_limited"] = _is_rate_limited(results[0])
            engine_failures.append("github")
            structured_log("engine_failed", run_id=run_id, engine="github", error=str(results[0]), rate_limited=github_result["rate_limited"])
        else:
            github_result = _stamp_ok(results[0])
            try:
                db.add(GitHubAnalysis(
                    username=username, run_id=run_id,
                    raw_metrics=github_result["raw_metrics"],
                    normalized_score=github_result["normalized_score"],
                    explanation=github_result["explanation"],
                    analysis_version=analysis_version,
                ))
                await db.commit()
                structured_log("engine_complete", run_id=run_id, engine="github", score=github_result["normalized_score"])
            except Exception:
                logger.exception(f"[{run_id}] Engine 1 (GitHub) DB save failed")
                await db.rollback()

        # ── Process Engine 1b: Advanced GitHub ────────────────
        if isinstance(results[1], Exception):
            logger.exception(f"[{run_id}] Engine 1b (Advanced) FAILED for {username}: {results[1]}")
            advanced_result["failure_reason"] = str(results[1])
            advanced_result["rate_limited"] = _is_rate_limited(results[1])
            engine_failures.append("advanced_github")
            structured_log("engine_failed", run_id=run_id, engine="advanced_github", error=str(results[1]))
        else:
            advanced_result = _stamp_ok(results[1])
            try:
                db.add(AdvancedGitHubAnalysis(
                    username=username, run_id=run_id,
                    raw_metrics=advanced_result["raw_metrics"],
                    anomaly_score=advanced_result["anomaly_score"],
                    explanation=advanced_result["explanation"],
                    analysis_version=analysis_version,
                ))
                await db.commit()
                structured_log("engine_complete", run_id=run_id, engine="advanced_github", anomaly_score=advanced_result["anomaly_score"])
            except Exception:
                logger.exception(f"[{run_id}] Engine 1b (Advanced) DB save failed")
                await db.rollback()

        # ── Process Engine 2: Profile Consistency ─────────────
        if isinstance(results[2], Exception):
            logger.exception(f"[{run_id}] Engine 2 (Profile) FAILED for {username}: {results[2]}")
            profile_result["failure_reason"] = str(results[2])
            engine_failures.append("profile")
            structured_log("engine_failed", run_id=run_id, engine="profile", error=str(results[2]))
        else:
            profile_result = _stamp_ok(results[2])
            try:
                db.add(ProfileConsistency(
                    username=username, run_id=run_id,
                    raw_metrics=profile_result["raw_metrics"],
                    normalized_score=profile_result["normalized_score"],
                    explanation=profile_result["explanation"],
                    analysis_version=analysis_version,
                ))
                await db.commit()
                structured_log("engine_complete", run_id=run_id, engine="profile", score=profile_result["normalized_score"])
            except Exception:
                logger.exception(f"[{run_id}] Engine 2 (Profile) DB save failed")
                await db.rollback()

        # ── Process Engine 3: LeetCode ────────────────────────
        if not leetcode_username:
            logger.info(f"[{run_id}] Engine 3 (LeetCode) skipped: no username provided")
            structured_log("engine_skipped", run_id=run_id, engine="leetcode", reason="no_username")
        elif isinstance(results[3], Exception):
            logger.exception(f"[{run_id}] Engine 3 (LeetCode) FAILED for {username}: {results[3]}")
            leetcode_result["failure_reason"] = str(results[3])
            leetcode_result["rate_limited"] = _is_rate_limited(results[3])
            engine_failures.append("leetcode")
            structured_log("engine_failed", run_id=run_id, engine="leetcode", error=str(results[3]))
        else:
            leetcode_result = _stamp_ok(results[3])
            try:
                db.add(LeetCodeAnalysis(
                    username=username, run_id=run_id,
                    raw_metrics=leetcode_result["raw_metrics"],
                    normalized_score=leetcode_result["normalized_score"],
                    explanation=leetcode_result["explanation"],
                    analysis_version=analysis_version,
                ))
                await db.commit()
                structured_log("engine_complete", run_id=run_id, engine="leetcode", score=leetcode_result["normalized_score"])
            except Exception:
                logger.exception(f"[{run_id}] Engine 3 (LeetCode) DB save failed")
                await db.rollback()

        # ── Process Engine 5: Product Mindset ─────────────────
        if isinstance(results[4], Exception):
            logger.exception(f"[{run_id}] Engine 5 (ProductMindset) FAILED for {username}: {results[4]}")
            mindset_result["failure_reason"] = str(results[4])
            engine_failures.append("product_mindset")
            structured_log("engine_failed", run_id=run_id, engine="product_mindset", error=str(results[4]))
        else:
            mindset_result = _stamp_ok(results[4])
            try:
                db.add(ProductMindsetAnalysis(
                    username=username, run_id=run_id,
                    raw_metrics=mindset_result["raw_metrics"],
                    normalized_score=mindset_result["normalized_score"],
                    explanation=mindset_result["explanation"],
                    analysis_version=analysis_version,
                ))
                await db.commit()
                structured_log("engine_complete", run_id=run_id, engine="product_mindset", score=mindset_result["normalized_score"])
            except Exception:
                logger.exception(f"[{run_id}] Engine 5 (ProductMindset) DB save failed")
                await db.rollback()

        # ── Process Engine 6: Digital Footprint ───────────────
        if results[5] is None:
            logger.info(f"[{run_id}] Engine 6 (DigitalFootprint) skipped: engine not available")
            structured_log("engine_skipped", run_id=run_id, engine="digital_footprint", reason="not_available")
        elif isinstance(results[5], Exception):
            logger.exception(f"[{run_id}] Engine 6 (DigitalFootprint) FAILED for {username}: {results[5]}")
            digital_result["failure_reason"] = str(results[5])
            digital_result["rate_limited"] = _is_rate_limited(results[5])
            engine_failures.append("digital_footprint")
            structured_log("engine_failed", run_id=run_id, engine="digital_footprint", error=str(results[5]))
        else:
            digital_result = _stamp_ok(results[5])
            try:
                db.add(DigitalFootprintAnalysis(
                    username=username, run_id=run_id,
                    raw_metrics=digital_result["raw_metrics"],
                    normalized_score=digital_result["normalized_score"],
                    explanation=digital_result["explanation"],
                    analysis_version=analysis_version,
                ))
                await db.commit()
                structured_log("engine_complete", run_id=run_id, engine="digital_footprint", score=digital_result["normalized_score"])
            except Exception:
                logger.exception(f"[{run_id}] Engine 6 (DigitalFootprint) DB save failed")
                await db.rollback()

        # ── Process Engine 8: ATS Intelligence ────────────────
        if results[6] is None:
            logger.info(f"[{run_id}] Engine 8 (ATS) skipped: no resume_text provided")
            structured_log("engine_skipped", run_id=run_id, engine="ats_intelligence", reason="no_resume_text")
        elif isinstance(results[6], Exception):
            logger.exception(f"[{run_id}] Engine 8 (ATS) FAILED for {username}: {results[6]}")
            ats_result["failure_reason"] = str(results[6])
            engine_failures.append("ats_intelligence")
            structured_log("engine_failed", run_id=run_id, engine="ats_intelligence", error=str(results[6]))
        else:
            ats_result = _stamp_ok(results[6])
            # Post-parallel cross-validation with now-available engine scores
            try:
                github_score = github_result.get("normalized_score", 0) if not github_result.get("engine_failed") else 0
                mindset_score = mindset_result.get("normalized_score", 0) if not mindset_result.get("engine_failed") else 0
                if github_score or mindset_score:
                    cv_penalty = self.ats_engine._cross_validate(
                        ats_result.get("raw_metrics", {}),
                        github_score,
                        mindset_score,
                    )
                    old_penalty = ats_result.get("raw_metrics", {}).get("cross_validation_penalty", 0)
                    if cv_penalty != old_penalty:
                        ats_result["raw_metrics"]["cross_validation_penalty"] = cv_penalty
                        ats_result["raw_metrics"]["cross_validation_penalty_sources"] = {
                            "github_score": github_score,
                            "product_mindset_score": mindset_score,
                        }
                        # Recompute final score
                        rm = ats_result["raw_metrics"]
                        weighted = (
                            rm.get("structure_score", 0) * 0.25
                            + rm.get("skill_authenticity_score", 0) * 0.25
                            + rm.get("role_alignment_score", 0) * 0.15
                            + rm.get("career_consistency_score", 0) * 0.15
                            + rm.get("parse_score", 0) * 0.10
                            + rm.get("readability_score", 0) * 0.10
                        )
                        ats_result["normalized_score"] = round(max(0, min(100, weighted - cv_penalty)), 1)
                        rm["final_score"] = ats_result["normalized_score"]
            except Exception:
                logger.exception(f"[{run_id}] Engine 8 (ATS) cross-validation update failed")

            try:
                db.add(ATSResumeAnalysis(
                    username=username,
                    run_id=run_id,
                    normalized_score=ats_result["normalized_score"],
                    structure_score=ats_result["raw_metrics"].get("structure_score", 0),
                    parse_score=ats_result["raw_metrics"].get("parse_score", 0),
                    skill_authenticity_score=ats_result["raw_metrics"].get("skill_authenticity_score", 0),
                    role_alignment_score=ats_result["raw_metrics"].get("role_alignment_score", 0),
                    career_consistency_score=ats_result["raw_metrics"].get("career_consistency_score", 0),
                    keyword_stuffing_risk=ats_result["raw_metrics"].get("keyword_stuffing_risk", "low"),
                    recruiter_readability=ats_result["raw_metrics"].get("recruiter_readability", "Unknown"),
                    cross_validation_penalty=ats_result["raw_metrics"].get("cross_validation_penalty", 0),
                    raw_metrics=ats_result["raw_metrics"],
                    explanation=ats_result["explanation"],
                    analysis_version=analysis_version,
                ))
                await db.commit()
                structured_log("engine_complete", run_id=run_id, engine="ats_intelligence", score=ats_result["normalized_score"])
            except Exception:
                logger.exception(f"[{run_id}] Engine 8 (ATS) DB save failed")
                await db.rollback()

        # ── Engine 4: Red Flags (sequential — needs upstream) ─
        redflag_result: Dict[str, Any] = {
            "raw_flags": {"flags": [], "total_flags": 0, "risk_level": "UNKNOWN"},
            "severity_score": 0.0,
            "explanation": {},
            "engine_failed": True,
            "failure_reason": None,
            "rate_limited": False,
        }
        rf_timer = TimerContext()
        try:
            with rf_timer:
                redflag_result = _stamp_ok(await _with_timeout(
                    self.redflag_engine.analyze(
                        username,
                        github_result["raw_metrics"],
                        profile_result["raw_metrics"],
                        leetcode_result["raw_metrics"],
                        advanced=advanced_result["raw_metrics"],
                    ),
                    f"[{run_id}] Engine 4 (RedFlag)",
                ))
            db.add(RedFlagAnalysis(
                username=username, run_id=run_id,
                raw_flags=redflag_result["raw_flags"],
                severity_score=redflag_result["severity_score"],
                explanation=redflag_result["explanation"],
                analysis_version=analysis_version,
            ))
            await db.commit()
            structured_log("engine_complete", run_id=run_id, engine="redflag", severity=redflag_result["severity_score"], duration_ms=rf_timer.elapsed_ms)
        except Exception as exc:
            logger.exception(f"[{run_id}] Engine 4 (RedFlag) FAILED for {username}")
            redflag_result["failure_reason"] = str(exc)
            engine_failures.append("redflag")
            structured_log("engine_failed", run_id=run_id, engine="redflag", error=str(exc), duration_ms=rf_timer.elapsed_ms)
            await db.rollback()

        # ── Gate 3: Consent enforcement (PST aggregation level) ──
        if self._job_id:
            _consent = (
                await db.execute(
                    select(UserConsent).where(
                        UserConsent.job_id == self._job_id
                    )
                )
            ).scalar_one_or_none()
            if _consent is None:
                logger.error(
                    "[%s] Gate 3 consent check failed — no UserConsent "
                    "row for job_id=%s. Skipping PST + report.",
                    run_id,
                    self._job_id,
                )
                raise RuntimeError(
                    "Consent audit record missing — PST aggregation blocked."
                )

        # ── Engine 7: PST Aggregation ─────────────────────────
        pst_result: Dict[str, Any] = {
            "username": username, "role_level": role_level,
            "component_scores": {}, "pst_score": 0.0,
            "trust_level": "Error", "explanation": {},
        }
        pst_timer = TimerContext()
        try:
            with pst_timer:
                pst_result = await _with_timeout(
                    self.pst_engine.analyze(
                        username, role_level, db,
                        run_id=run_id, engine_failures=engine_failures,
                    ),
                    f"[{run_id}] Engine 7 (PST)",
                    timeout=10.0,
                )
            db.add(PSTReport(
                username=pst_result["username"],
                run_id=run_id,
                role_level=pst_result["role_level"],
                component_scores=pst_result["component_scores"],
                pst_score=pst_result["pst_score"],
                trust_level=pst_result["trust_level"],
                explanation=pst_result["explanation"],
                analysis_version=analysis_version,
            ))
            await db.commit()
            structured_log("engine_complete", run_id=run_id, engine="pst", score=pst_result["pst_score"], trust_level=pst_result["trust_level"], duration_ms=pst_timer.elapsed_ms)
        except Exception as exc:
            logger.exception(f"[{run_id}] Engine 7 (PST) FAILED for {username}")
            engine_failures.append("pst")
            structured_log("engine_failed", run_id=run_id, engine="pst", error=str(exc), duration_ms=pst_timer.elapsed_ms)
            await db.rollback()

        # ── Recruiter Report ──────────────────────────────────
        try:
            report_result = await _with_timeout(
                self.report_engine.generate(username, db, run_id=run_id),
                f"[{run_id}] Recruiter report",
                timeout=10.0,
            )
            db.add(RecruiterReport(
                username=username, run_id=run_id,
                report_data=report_result,
                analysis_version=analysis_version,
            ))
            await db.commit()
            structured_log("engine_complete", run_id=run_id, engine="recruiter_report")
        except Exception:
            logger.exception(f"[{run_id}] Recruiter report FAILED for {username}")
            await db.rollback()

        if engine_failures:
            logger.warning(f"[{run_id}] Pipeline completed with failures: {engine_failures}")
        else:
            logger.info(f"[{run_id}] Full pipeline completed successfully for {username}")

        structured_log("pipeline_complete", run_id=run_id, username=username, engine_failures=engine_failures, analysis_version=analysis_version)

        return {
            "run_id": run_id,
            "username": username,
            "role_level": role_level,
            "analysis_version": analysis_version,
            "github": github_result,
            "advanced_github": advanced_result,
            "profile_consistency": profile_result,
            "leetcode": leetcode_result,
            "product_mindset": mindset_result,
            "digital_footprint": digital_result,
            "ats_intelligence": ats_result,
            "redflags": redflag_result,
            "pst_report": pst_result,
            "engine_failures": engine_failures,
        }
