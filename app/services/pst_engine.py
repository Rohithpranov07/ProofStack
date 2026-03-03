"""ENGINE 7 — PST Master Aggregation Engine.

ProofStack Trust Score orchestrator.
Reads the results from Engines 1-6 (for the same run_id) from the database
and produces a single weighted trust score.

Deterministic scoring formula (true 0-100 scale):
  base_score = Σ(engine_i * W_i) where Σ(W_i) == 1.0 always
  penalty    = redflag_severity * W_penalty
  pst_score  = clamp(base_score - penalty, 0, 100)

  If severity >= 70: pst_score = min(pst_score, 50)   (hard cap)
  If severity >= 85: pst_score = min(pst_score, 35)   (critical cap)

Escalation rules (Phase 2):
  - anomaly_score >= 60  → reduce PST by 15 %
  - product_mindset < 20 AND GitHub burst detected → −10 penalty
  - All escalation triggers are logged in ``escalation_reasons``.

Role weights (positive sum to 1.0):
  entry:  gh=0.20  pr=0.18  lc=0.18  pm=0.14  df=0.18  ats=0.12  penalty=0.15
  mid:    gh=0.25  pr=0.17  lc=0.13  pm=0.18  df=0.15  ats=0.12  penalty=0.15
  senior: gh=0.25  pr=0.17  lc=0.08  pm=0.22  df=0.16  ats=0.12  penalty=0.20

Trust bands:
  >=80 Highly Verified | >=65 Strong | >=45 Moderate | >=25 Weak | <25 High Risk

Engine failure handling:
  - If an engine row is missing or its ``normalized_score IS NULL``,
    its weight is **removed** and the remaining weights are
    redistributed proportionally so they still sum to 1.0.
  - A ``confidence_reduction`` metadata field records the percentage of
    total weight that was dropped, so downstream consumers know how
    reliable the aggregate is.

Run-aware: uses run_id to prevent concurrent contamination.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger, structured_log
from app.db.models import (
    AdvancedGitHubAnalysis,
    GitHubAnalysis,
    LeetCodeAnalysis,
    ProductMindsetAnalysis,
    ProfileConsistency,
    RedFlagAnalysis,
)

# ── try importing the new Digital Footprint model ───────────
try:
    from app.db.models import DigitalFootprintAnalysis  # type: ignore[attr-defined]
    _HAS_DIGITAL_FOOTPRINT = True
except ImportError:
    _HAS_DIGITAL_FOOTPRINT = False

# ── try importing the ATS Resume Analysis model ────────────
try:
    from app.db.models import ATSResumeAnalysis  # type: ignore[attr-defined]
    _HAS_ATS = True
except ImportError:
    _HAS_ATS = False


class PSTAggregationEngine:
    """Orchestrator: reads engine results from DB -> deterministic trust score."""

    # ── public entry-point ────────────────────────────────────

    async def analyze(
        self,
        username: str,
        role_level: str,
        db: AsyncSession,
        *,
        run_id: Optional[str] = None,
        engine_failures: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Aggregate scores with graceful degradation.

        Args:
            run_id: If provided, queries only results from this run.
            engine_failures: List of engine names that failed during
                this pipeline run (used alongside DB lookup to mark
                an engine as unavailable).
        """
        engine_failures = engine_failures or []
        logger.info(
            f"Starting PST aggregation for {username} "
            f"(role: {role_level}, run_id: {run_id}, failures: {engine_failures})"
        )

        # Fetch rows ──────────────────────────────────────────
        github = await self._get_result(db, GitHubAnalysis, username, run_id)
        profile = await self._get_result(db, ProfileConsistency, username, run_id)
        leetcode = await self._get_result(db, LeetCodeAnalysis, username, run_id)
        mindset = await self._get_result(db, ProductMindsetAnalysis, username, run_id)
        digital = (
            await self._get_result(db, DigitalFootprintAnalysis, username, run_id)
            if _HAS_DIGITAL_FOOTPRINT
            else None
        )
        ats = (
            await self._get_result(db, ATSResumeAnalysis, username, run_id)
            if _HAS_ATS
            else None
        )
        redflags = await self._get_result(db, RedFlagAnalysis, username, run_id)

        # Fetch advanced GitHub for anomaly_score escalation ──
        advanced = await self._get_result(db, AdvancedGitHubAnalysis, username, run_id)

        weights = self._get_weights(role_level)

        # ── Collect available engines & apply failure filter ──
        engine_map: Dict[str, Any] = {
            "github": github,
            "profile": profile,
            "leetcode": leetcode,
            "product_mindset": mindset,
            "digital_footprint": digital,
            "ats": ats,
        }

        available: Dict[str, float] = {}
        scores: Dict[str, float] = {}
        failed_engines: List[str] = []

        for key, row in engine_map.items():
            w = weights.get(key, 0.0)
            if w == 0.0:
                continue  # not part of weight table for this role
            if key in engine_failures:
                failed_engines.append(key)
                continue
            if row is None:
                failed_engines.append(key)
                continue
            ns = getattr(row, "normalized_score", None)
            if ns is None:
                failed_engines.append(key)
                continue
            available[key] = w
            scores[key] = float(ns)

        if not available:
            return self._empty(username, role_level)

        # ── Redistribute weights proportionally ──────────────
        original_weight_sum = sum(weights.get(k, 0) for k in engine_map if weights.get(k, 0) > 0)
        available_weight_sum = sum(available.values())
        dropped_weight = original_weight_sum - available_weight_sum
        confidence_reduction = round((dropped_weight / original_weight_sum) * 100, 2) if original_weight_sum else 0.0

        norm_w: Dict[str, float] = {k: v / available_weight_sum for k, v in available.items()}

        if failed_engines:
            logger.warning(
                f"[PST] Weight redistribution for {username}: "
                f"removed={failed_engines}, confidence_reduction={confidence_reduction}%"
            )

        # ── Weighted base score ──────────────────────────────
        weighted_score = sum(scores[k] * norm_w[k] for k in available)

        # ── Red-flag penalty ─────────────────────────────────
        rf_severity = redflags.severity_score if redflags else 0.0
        penalty = rf_severity * weights["redflag_penalty"]

        pst_score = round(max(0.0, min(weighted_score - penalty, 100.0)), 2)

        # ── Phase 2: Red-flag escalation hard caps ───────────
        cap_applied: Optional[str] = None
        escalation_reasons: List[str] = []

        if rf_severity >= 85:
            if pst_score > 35:
                pst_score = 35.0
                cap_applied = "critical_cap_35"
                escalation_reasons.append(f"severity {rf_severity} >= 85 → capped at 35")
                logger.warning(f"[PST] Critical red-flag cap applied for {username}: severity={rf_severity}")
        elif rf_severity >= 70:
            if pst_score > 50:
                pst_score = 50.0
                cap_applied = "high_risk_cap_50"
                escalation_reasons.append(f"severity {rf_severity} >= 70 → capped at 50")
                logger.warning(f"[PST] High-risk red-flag cap applied for {username}: severity={rf_severity}")

        # ── Phase 2: Anomaly-score escalation ────────────────
        anomaly_score = getattr(advanced, "anomaly_score", 0.0) or 0.0 if advanced else 0.0
        if anomaly_score >= 60:
            reduction = round(pst_score * 0.15, 2)
            pst_score = round(max(0.0, pst_score - reduction), 2)
            escalation_reasons.append(
                f"anomaly_score {anomaly_score} >= 60 → reduced by 15% ({reduction} pts)"
            )
            logger.warning(
                f"[PST] Anomaly escalation for {username}: "
                f"anomaly={anomaly_score}, reduced by {reduction}"
            )

        # ── Phase 2: Product-mindset + burst penalty ─────────
        mindset_score_val = scores.get("product_mindset", 100.0)
        # Detect GitHub burst via advanced metrics
        burst_detected = False
        if advanced:
            adv_raw = getattr(advanced, "raw_metrics", None) or {}
            adv_expl = getattr(advanced, "explanation", None) or {}
            # burst = most commits in single day > 60% of total, or explicit flag
            burst_detected = (
                adv_expl.get("burst_detected", False)
                or adv_raw.get("burst_ratio", 0) > 0.6
            )
        if mindset_score_val < 20 and burst_detected:
            pst_score = round(max(0.0, pst_score - 10), 2)
            escalation_reasons.append(
                f"product_mindset={mindset_score_val} (<20) AND burst_detected → −10 penalty"
            )
            logger.warning(
                f"[PST] Burst + low-mindset penalty for {username}: "
                f"mindset={mindset_score_val}"
            )

        # ── Final clamp (safety) ─────────────────────────────
        pst_score = round(max(0.0, min(pst_score, 100.0)), 2)

        trust_level = self._classify_trust(pst_score)

        if escalation_reasons:
            structured_log(
                "pst_escalation",
                run_id=run_id,
                username=username,
                escalation_reasons=escalation_reasons,
                final_score=pst_score,
            )

        # ── Build return dicts ───────────────────────────────
        component_scores: Dict[str, Any] = {
            "github_score": scores.get("github"),
            "profile_score": scores.get("profile"),
            "leetcode_score": scores.get("leetcode"),
            "product_mindset_score": scores.get("product_mindset"),
            "digital_footprint_score": scores.get("digital_footprint"),
            "ats_score": scores.get("ats"),
            "redflag_severity": rf_severity,
            "anomaly_score": anomaly_score,
            "engines_available": list(available.keys()),
            "engines_failed": failed_engines,
        }

        explanation: Dict[str, Any] = {
            "weighting_used": {k: round(v, 4) for k, v in norm_w.items()},
            "original_weights": weights,
            "weighted_score_before_penalty": round(weighted_score, 2),
            "penalty_deduction": round(penalty, 2),
            "final_score": pst_score,
            "trust_level": trust_level,
            "degraded": len(available) < len([w for w in weights if w != "redflag_penalty" and weights[w] > 0]),
            "confidence_reduction_pct": confidence_reduction,
            "cap_applied": cap_applied,
            "escalation_reasons": escalation_reasons,
            "anomaly_score": anomaly_score,
            "run_id": run_id,
        }

        if cap_applied:
            explanation["cap_reason"] = (
                "High-risk anomalies detected — score capped."
            )

        return {
            "username": username,
            "role_level": role_level,
            "component_scores": component_scores,
            "pst_score": pst_score,
            "trust_level": trust_level,
            "explanation": explanation,
        }

    # ── DB helpers ────────────────────────────────────────────

    @staticmethod
    async def _get_result(
        db: AsyncSession, model: Any, username: str, run_id: Optional[str]
    ) -> Optional[Any]:
        """Fetch engine result — by run_id if available, else latest row."""
        if run_id:
            result = await db.execute(
                select(model)
                .where(model.username == username, model.run_id == run_id)
                .order_by(model.id.desc())
                .limit(1)
            )
        else:
            result = await db.execute(
                select(model)
                .where(model.username == username)
                .order_by(model.id.desc())
                .limit(1)
            )
        return result.scalar_one_or_none()

    # ── Weight tables ─────────────────────────────────────────

    @staticmethod
    def _get_weights(role_level: str) -> Dict[str, float]:
        """Positive weights sum to 1.0. Penalty is separate."""
        if role_level == "entry":
            return {
                "github": 0.20, "profile": 0.18, "leetcode": 0.18,
                "product_mindset": 0.14, "digital_footprint": 0.18,
                "ats": 0.12,
                "redflag_penalty": 0.15,
            }
        if role_level == "senior":
            return {
                "github": 0.25, "profile": 0.17, "leetcode": 0.08,
                "product_mindset": 0.22, "digital_footprint": 0.16,
                "ats": 0.12,
                "redflag_penalty": 0.20,
            }
        # mid (default)
        return {
            "github": 0.25, "profile": 0.17, "leetcode": 0.13,
            "product_mindset": 0.18, "digital_footprint": 0.15,
            "ats": 0.12,
            "redflag_penalty": 0.15,
        }

    @staticmethod
    def _classify_trust(score: float) -> str:
        if score >= 80:
            return "Highly Verified"
        elif score >= 65:
            return "Strong"
        elif score >= 45:
            return "Moderate"
        elif score >= 25:
            return "Weak"
        return "High Risk"

    @staticmethod
    def _empty(username: str, role_level: str) -> Dict[str, Any]:
        return {
            "username": username,
            "role_level": role_level,
            "component_scores": {},
            "pst_score": 0.0,
            "trust_level": "Insufficient Data",
            "explanation": {"error": "No engine data available"},
        }
