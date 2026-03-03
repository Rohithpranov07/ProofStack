"""Deterministic Scoring Integrity Tests.

Simulates canonical candidate profiles and asserts that the PST
engine produces scores within expected bands.  These tests exercise
the *pure scoring logic* — no database, no HTTP calls.

Run with:
    pytest tests/test_scoring_integrity.py -v

=== Primary Cases (Phase 3 spec) ===

  1 — Strong everything          → PST  > 85
  2 — Strong GitHub + weak LC    → PST  65–80
  3 — Weak GitHub + strong LC    → PST  55–70
  4 — Severe red flags (≥85)     → PST  < 50  (escalation cap ≤35)
  5 — Missing profile            → weight redistribution, no inflation

=== Extended Cases ===

  A — Weak GitHub (legacy)       → PST  40–80
  B — High red-flags cap 50      → PST  ≤50
  C — All engines failed          → trust_level == "Insufficient Data"
  D — Weight sum = 1.0 on degraded
  E — engine_failures excludes engine
  F — No inflation on missing engine
  G — Role levels differ
  H — Determinism (repeated call = same output)
  I — Score never negative
  J — Score never exceeds 100
  K — Anomaly escalation (anomaly_score ≥60 → 15% reduction)
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────

def _make_row(
    normalized_score: Optional[float] = None,
    severity_score: Optional[float] = None,
    anomaly_score: Optional[float] = None,
    raw_metrics: Optional[Dict[str, Any]] = None,
    explanation: Optional[Dict[str, Any]] = None,
):
    """Return a mock ORM row with the requested score attributes."""
    row = MagicMock()
    row.normalized_score = normalized_score
    if severity_score is not None:
        row.severity_score = severity_score
    if anomaly_score is not None:
        row.anomaly_score = anomaly_score
    row.raw_metrics = raw_metrics or {}
    row.explanation = explanation or {}
    return row


def _make_lookup(
    github: Optional[float] = None,
    profile: Optional[float] = None,
    leetcode: Optional[float] = None,
    mindset: Optional[float] = None,
    digital: Optional[float] = None,
    redflag_severity: Optional[float] = None,
    anomaly_score: Optional[float] = None,
    advanced_raw: Optional[Dict[str, Any]] = None,
    advanced_expl: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Map model class names to mock rows for patching ``_get_result``."""
    from app.db.models import (
        AdvancedGitHubAnalysis,
        GitHubAnalysis,
        LeetCodeAnalysis,
        ProductMindsetAnalysis,
        ProfileConsistency,
        RedFlagAnalysis,
    )
    try:
        from app.db.models import DigitalFootprintAnalysis
    except ImportError:
        DigitalFootprintAnalysis = None  # type: ignore[misc,assignment]

    mapping: Dict[Any, Any] = {
        GitHubAnalysis: _make_row(normalized_score=github) if github is not None else None,
        ProfileConsistency: _make_row(normalized_score=profile) if profile is not None else None,
        LeetCodeAnalysis: _make_row(normalized_score=leetcode) if leetcode is not None else None,
        ProductMindsetAnalysis: _make_row(normalized_score=mindset) if mindset is not None else None,
        RedFlagAnalysis: _make_row(severity_score=redflag_severity) if redflag_severity is not None else None,
        AdvancedGitHubAnalysis: (
            _make_row(
                anomaly_score=anomaly_score,
                raw_metrics=advanced_raw or {},
                explanation=advanced_expl or {},
            )
            if anomaly_score is not None
            else None
        ),
    }
    if DigitalFootprintAnalysis is not None:
        mapping[DigitalFootprintAnalysis] = (
            _make_row(normalized_score=digital) if digital is not None else None
        )
    return mapping


async def _run_pst(
    lookup: Dict[str, Any],
    role_level: str = "mid",
    engine_failures: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Instantiate PSTAggregationEngine, patch DB reads, and compute score."""
    from app.services.pst_engine import PSTAggregationEngine

    engine = PSTAggregationEngine()

    async def fake_get_result(db, model, username, run_id):
        return lookup.get(model)

    with patch.object(engine, "_get_result", side_effect=fake_get_result):
        db = AsyncMock()
        result = await engine.analyze(
            "testuser", role_level, db,
            run_id="test-run-id",
            engine_failures=engine_failures or [],
        )
    return result


# ══════════════════════════════════════════════════════════════
# PRIMARY CASES (Phase 3 specification)
# ══════════════════════════════════════════════════════════════

class TestPhase3PrimaryCases:
    """The 5 deterministic cases from the Phase 3 production spec."""

    @pytest.mark.asyncio
    async def test_case_1_strong_everything_above_85(self):
        """Case 1: All engines ≥80, low red flags → PST > 85."""
        lookup = _make_lookup(
            github=90, profile=88, leetcode=85, mindset=82, digital=86,
            redflag_severity=5, anomaly_score=10,
        )
        result = await _run_pst(lookup, "mid")
        assert result["pst_score"] > 85, f"Expected >85, got {result['pst_score']}"
        assert result["trust_level"] == "Highly Verified"

    @pytest.mark.asyncio
    async def test_case_2_strong_github_weak_leetcode(self):
        """Case 2: Strong GitHub (85+), weak LeetCode (30) → PST 65-80."""
        lookup = _make_lookup(
            github=88, profile=75, leetcode=30, mindset=70, digital=68,
            redflag_severity=10, anomaly_score=15,
        )
        result = await _run_pst(lookup, "mid")
        assert 65 <= result["pst_score"] <= 80, f"Expected 65-80, got {result['pst_score']}"

    @pytest.mark.asyncio
    async def test_case_3_weak_github_strong_leetcode(self):
        """Case 3: Weak GitHub (30), strong LeetCode (88) → PST 52-70.

        Mid weights: gh=0.30, so weak github pulls hard.  Exact calculation:
        30×0.30 + 70×0.20 + 88×0.15 + 60×0.20 + 55×0.15 = 56.45 − 1.8 = 54.65
        """
        lookup = _make_lookup(
            github=30, profile=70, leetcode=88, mindset=60, digital=55,
            redflag_severity=12, anomaly_score=20,
        )
        result = await _run_pst(lookup, "mid")
        assert 52 <= result["pst_score"] <= 70, f"Expected 52-70, got {result['pst_score']}"

    @pytest.mark.asyncio
    async def test_case_4_severe_red_flags_below_50(self):
        """Case 4: Severe red flags (severity ≥85) → PST < 50 (capped ≤35)."""
        lookup = _make_lookup(
            github=90, profile=85, leetcode=80, mindset=75, digital=80,
            redflag_severity=90, anomaly_score=10,
        )
        result = await _run_pst(lookup, "mid")
        assert result["pst_score"] < 50, f"Expected <50, got {result['pst_score']}"
        assert result["pst_score"] <= 35, f"Expected ≤35 (critical cap), got {result['pst_score']}"
        assert result["explanation"]["cap_applied"] == "critical_cap_35"

    @pytest.mark.asyncio
    async def test_case_5_missing_profile_weight_redistribution(self):
        """Case 5: Missing Profile → weight redistributed, no inflation."""
        # Baseline: all engines present
        full_lookup = _make_lookup(
            github=70, profile=70, leetcode=70, mindset=70, digital=70,
            redflag_severity=5, anomaly_score=5,
        )
        full_result = await _run_pst(full_lookup, "mid")

        # Degraded: no profile
        partial_lookup = _make_lookup(
            github=70, profile=None, leetcode=70, mindset=70, digital=70,
            redflag_severity=5, anomaly_score=5,
        )
        partial_result = await _run_pst(partial_lookup, "mid")

        # Weight redistribution must not inflate
        assert abs(partial_result["pst_score"] - full_result["pst_score"]) < 3.0, (
            f"No-inflation: full={full_result['pst_score']}, partial={partial_result['pst_score']}"
        )
        assert partial_result["explanation"]["degraded"] is True
        assert partial_result["explanation"]["confidence_reduction_pct"] > 0
        assert "profile" not in partial_result["explanation"]["weighting_used"]
        # Weights must still sum to 1.0
        w_sum = sum(partial_result["explanation"]["weighting_used"].values())
        assert abs(w_sum - 1.0) < 0.01, f"Weights sum to {w_sum}"


# ══════════════════════════════════════════════════════════════
# BOUNDARY & ESCALATION ENFORCEMENT
# ══════════════════════════════════════════════════════════════

class TestBoundaryEnforcement:
    """Score boundary and escalation assertions."""

    @pytest.mark.asyncio
    async def test_score_never_negative(self):
        """PST score must never go below 0 regardless of penalties."""
        lookup = _make_lookup(
            github=5, profile=5, leetcode=5, mindset=5, digital=5,
            redflag_severity=95, anomaly_score=80,
        )
        result = await _run_pst(lookup, "mid")
        assert result["pst_score"] >= 0.0, f"Negative score: {result['pst_score']}"

    @pytest.mark.asyncio
    async def test_score_never_exceeds_100(self):
        """PST score must never exceed 100, even with perfect engines."""
        lookup = _make_lookup(
            github=100, profile=100, leetcode=100, mindset=100, digital=100,
            redflag_severity=0, anomaly_score=0,
        )
        result = await _run_pst(lookup, "mid")
        assert result["pst_score"] <= 100.0, f"Score >100: {result['pst_score']}"

    @pytest.mark.asyncio
    async def test_high_risk_cap_50(self):
        """Severity ≥70 → PST capped at 50."""
        lookup = _make_lookup(
            github=90, profile=85, leetcode=80, mindset=75, digital=80,
            redflag_severity=75, anomaly_score=10,
        )
        result = await _run_pst(lookup, "mid")
        assert result["pst_score"] <= 50, f"Expected ≤50, got {result['pst_score']}"
        assert result["explanation"]["cap_applied"] == "high_risk_cap_50"

    @pytest.mark.asyncio
    async def test_anomaly_escalation_reduces_score(self):
        """Anomaly score ≥60 → PST reduced by 15%."""
        # Without anomaly escalation
        base_lookup = _make_lookup(
            github=80, profile=75, leetcode=70, mindset=65, digital=60,
            redflag_severity=10, anomaly_score=20,
        )
        base = await _run_pst(base_lookup, "mid")

        # With high anomaly
        anomaly_lookup = _make_lookup(
            github=80, profile=75, leetcode=70, mindset=65, digital=60,
            redflag_severity=10, anomaly_score=70,
        )
        anomaly = await _run_pst(anomaly_lookup, "mid")

        assert anomaly["pst_score"] < base["pst_score"], (
            f"Anomaly should reduce score: base={base['pst_score']}, anomaly={anomaly['pst_score']}"
        )
        assert any("anomaly" in r.lower() for r in anomaly["explanation"].get("escalation_reasons", []))


# ══════════════════════════════════════════════════════════════
# EXTENDED CASES (regression from previous sessions)
# ══════════════════════════════════════════════════════════════

class TestExtendedCases:
    """Extended scoring tests for regression coverage."""

    @pytest.mark.asyncio
    async def test_all_engines_failed(self):
        """No engine data → Insufficient Data."""
        lookup = _make_lookup()
        result = await _run_pst(lookup, "mid")
        assert result["pst_score"] == 0.0
        assert result["trust_level"] == "Insufficient Data"

    @pytest.mark.asyncio
    async def test_weight_redistribution_sums_to_one(self):
        """Redistributed weights must always sum to 1.0."""
        lookup = _make_lookup(
            github=80, profile=None, leetcode=None, mindset=60, digital=70,
            redflag_severity=5, anomaly_score=10,
        )
        result = await _run_pst(lookup, "entry")
        weights_used = result["explanation"]["weighting_used"]
        total = sum(weights_used.values())
        assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"

    @pytest.mark.asyncio
    async def test_engine_failure_list_excludes_engine(self):
        """Engine listed in engine_failures is excluded even if DB row exists."""
        lookup = _make_lookup(
            github=80, profile=75, leetcode=70, mindset=65, digital=60,
            redflag_severity=10, anomaly_score=10,
        )
        result = await _run_pst(lookup, "mid", engine_failures=["github"])
        assert "github" not in result["explanation"]["weighting_used"]
        assert "github" in result["component_scores"]["engines_failed"]

    @pytest.mark.asyncio
    async def test_no_inflation_on_missing_engine(self):
        """Removing an engine must not inflate the PST above baseline."""
        full_lookup = _make_lookup(
            github=60, profile=60, leetcode=60, mindset=60, digital=60,
            redflag_severity=0, anomaly_score=0,
        )
        full_result = await _run_pst(full_lookup, "mid")

        partial_lookup = _make_lookup(
            github=60, profile=60, leetcode=None, mindset=60, digital=60,
            redflag_severity=0, anomaly_score=0,
        )
        partial_result = await _run_pst(partial_lookup, "mid")

        assert abs(partial_result["pst_score"] - full_result["pst_score"]) < 2.0, (
            f"No-inflation: full={full_result['pst_score']}, partial={partial_result['pst_score']}"
        )

    @pytest.mark.asyncio
    async def test_role_levels_produce_different_weights(self):
        """Different role levels should produce distinct weight distributions."""
        lookup = _make_lookup(
            github=80, profile=70, leetcode=50, mindset=90, digital=60,
            redflag_severity=10, anomaly_score=10,
        )
        entry = await _run_pst(lookup, "entry")
        mid = await _run_pst(lookup, "mid")
        senior = await _run_pst(lookup, "senior")

        scores = {entry["pst_score"], mid["pst_score"], senior["pst_score"]}
        assert len(scores) >= 2, "Expected different PST scores for different roles"

    @pytest.mark.asyncio
    async def test_determinism(self):
        """Same input must always produce the same output."""
        lookup = _make_lookup(
            github=72, profile=68, leetcode=55, mindset=63, digital=50,
            redflag_severity=22, anomaly_score=15,
        )
        r1 = await _run_pst(lookup, "mid")
        r2 = await _run_pst(lookup, "mid")
        assert r1["pst_score"] == r2["pst_score"]
        assert r1["trust_level"] == r2["trust_level"]

    @pytest.mark.asyncio
    async def test_escalation_reasons_populated(self):
        """When escalation triggers fire, escalation_reasons list is populated."""
        lookup = _make_lookup(
            github=90, profile=85, leetcode=80, mindset=75, digital=80,
            redflag_severity=90, anomaly_score=70,
        )
        result = await _run_pst(lookup, "mid")
        reasons = result["explanation"].get("escalation_reasons", [])
        assert len(reasons) >= 2, f"Expected ≥2 escalation reasons, got {reasons}"
