"""Red Flag Engine – Unit Tests.

Tests the 14 deterministic flag types, severity scoring,
risk level classification, and edge cases — no network calls.

Run with:
    pytest tests/test_redflag_engine.py -v
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest

from app.services.redflag_engine import RedFlagEngine


# ── Helpers ───────────────────────────────────────────────

def _clean_github(**overrides) -> Dict[str, Any]:
    base = {
        "burst_flag": False,
        "commit_variance": 50.0,
        "average_contributors": 2.0,
    }
    base.update(overrides)
    return base


def _clean_profile(**overrides) -> Dict[str, Any]:
    base = {
        "experience_ratio": 0.9,
        "skill_ratio": 0.8,
        "project_ratio": 0.7,
        "linkedin_profile_verified": True,
    }
    base.update(overrides)
    return base


def _clean_leetcode(**overrides) -> Dict[str, Any]:
    base = {
        "total_solved": 100,
        "easy_ratio": 0.3,
        "acceptance_rate": 0.65,
    }
    base.update(overrides)
    return base


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Core flag tests ──────────────────────────────────────

class TestIndividualFlags:
    def setup_method(self):
        self.engine = RedFlagEngine()

    @pytest.mark.asyncio
    async def test_clean_profile_low_risk(self):
        result = await self.engine.analyze(
            "clean_user", _clean_github(), _clean_profile(), _clean_leetcode()
        )
        assert result["severity_score"] < 30
        assert result["explanation"]["risk_level"] == "LOW RISK"
        assert result["raw_flags"]["total_flags"] == 0

    @pytest.mark.asyncio
    async def test_commit_burst_flag(self):
        result = await self.engine.analyze(
            "burst_user",
            _clean_github(burst_flag=True),
            _clean_profile(),
            _clean_leetcode(),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Commit Burst Activity" in flags
        assert result["severity_score"] >= 20

    @pytest.mark.asyncio
    async def test_high_commit_variance_flag(self):
        result = await self.engine.analyze(
            "var_user",
            _clean_github(commit_variance=600),
            _clean_profile(),
            _clean_leetcode(),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "High Commit Variance" in flags

    @pytest.mark.asyncio
    async def test_experience_mismatch_flag(self):
        result = await self.engine.analyze(
            "exp_user",
            _clean_github(),
            _clean_profile(experience_ratio=0.3),
            _clean_leetcode(),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Experience Timeline Mismatch" in flags

    @pytest.mark.asyncio
    async def test_skill_evidence_weak_flag(self):
        result = await self.engine.analyze(
            "skill_user",
            _clean_github(),
            _clean_profile(skill_ratio=0.4),
            _clean_leetcode(),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Skill Evidence Weak" in flags

    @pytest.mark.asyncio
    async def test_project_not_found_flag(self):
        result = await self.engine.analyze(
            "project_user",
            _clean_github(),
            _clean_profile(project_ratio=0.3),
            _clean_leetcode(),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Project Not Found" in flags

    @pytest.mark.asyncio
    async def test_linkedin_not_verified_flag(self):
        result = await self.engine.analyze(
            "linkedin_user",
            _clean_github(),
            _clean_profile(linkedin_profile_verified=False),
            _clean_leetcode(),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "LinkedIn Not Verified" in flags

    @pytest.mark.asyncio
    async def test_leetcode_no_activity_flag(self):
        result = await self.engine.analyze(
            "lc_user",
            _clean_github(),
            _clean_profile(),
            _clean_leetcode(total_solved=0),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "LeetCode No Activity" in flags

    @pytest.mark.asyncio
    async def test_easy_dominant_flag(self):
        result = await self.engine.analyze(
            "easy_user",
            _clean_github(),
            _clean_profile(),
            _clean_leetcode(easy_ratio=0.85, total_solved=100),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Easy-Dominant Problem Solving" in flags

    @pytest.mark.asyncio
    async def test_low_acceptance_rate_flag(self):
        result = await self.engine.analyze(
            "acc_user",
            _clean_github(),
            _clean_profile(),
            _clean_leetcode(acceptance_rate=0.2),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Low Acceptance Rate" in flags

    @pytest.mark.asyncio
    async def test_no_collaboration_flag(self):
        result = await self.engine.analyze(
            "solo_user",
            _clean_github(average_contributors=1.0),
            _clean_profile(),
            _clean_leetcode(),
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "No Collaboration Evidence" in flags


# ── Advanced flags ────────────────────────────────────────

class TestAdvancedFlags:
    def setup_method(self):
        self.engine = RedFlagEngine()

    @pytest.mark.asyncio
    async def test_loc_anomaly_flag(self):
        result = await self.engine.analyze(
            "loc_user",
            _clean_github(),
            _clean_profile(),
            _clean_leetcode(),
            advanced={"loc_anomaly_ratio": 0.25},
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "LOC Anomaly Detected" in flags

    @pytest.mark.asyncio
    async def test_repetitive_messages_flag(self):
        result = await self.engine.analyze(
            "rep_user",
            _clean_github(),
            _clean_profile(),
            _clean_leetcode(),
            advanced={"repetitive_message_ratio": 0.5},
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Repetitive Commit Messages" in flags

    @pytest.mark.asyncio
    async def test_cross_repo_overlap_flag(self):
        result = await self.engine.analyze(
            "overlap_user",
            _clean_github(),
            _clean_profile(),
            _clean_leetcode(),
            advanced={"repo_overlap_score": 5},
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "Cross-Repo Commit Overlap" in flags


# ── Risk levels & scoring ─────────────────────────────────

class TestRiskLevels:
    def setup_method(self):
        self.engine = RedFlagEngine()

    @pytest.mark.asyncio
    async def test_high_risk_threshold(self):
        """Burst + experience mismatch + project not found + no collab + skill weak + loc anomaly → HIGH."""
        result = await self.engine.analyze(
            "risky_user",
            _clean_github(burst_flag=True, commit_variance=600, average_contributors=0.5),
            _clean_profile(experience_ratio=0.2, project_ratio=0.2, skill_ratio=0.3, linkedin_profile_verified=False),
            _clean_leetcode(acceptance_rate=0.2),
        )
        assert result["explanation"]["risk_level"] == "HIGH RISK"
        assert result["severity_score"] >= 60

    @pytest.mark.asyncio
    async def test_moderate_risk_threshold(self):
        """Burst + no collab + variance → MODERATE (20 + 5 + 10 = 35)."""
        result = await self.engine.analyze(
            "mod_user",
            _clean_github(burst_flag=True, commit_variance=600, average_contributors=0.5),
            _clean_profile(),
            _clean_leetcode(),
        )
        assert result["severity_score"] >= 30
        assert result["explanation"]["risk_level"] in ("MODERATE RISK", "HIGH RISK")

    @pytest.mark.asyncio
    async def test_severity_capped_at_100(self):
        """All possible flags → capped at 100."""
        result = await self.engine.analyze(
            "max_user",
            _clean_github(burst_flag=True, commit_variance=1000, average_contributors=0.5),
            _clean_profile(
                experience_ratio=0.1,
                skill_ratio=0.1,
                project_ratio=0.1,
                linkedin_profile_verified=False,
            ),
            _clean_leetcode(total_solved=0, easy_ratio=0.9, acceptance_rate=0.1),
            advanced={
                "loc_anomaly_ratio": 0.3,
                "repetitive_message_ratio": 0.6,
                "repo_overlap_score": 5,
            },
        )
        assert result["severity_score"] <= 100.0

    @pytest.mark.asyncio
    async def test_deterministic(self):
        """Same inputs → same severity score."""
        gh = _clean_github(burst_flag=True)
        prof = _clean_profile(skill_ratio=0.3)
        lc = _clean_leetcode()
        r1 = await self.engine.analyze("user", gh, prof, lc)
        r2 = await self.engine.analyze("user", gh, prof, lc)
        assert r1["severity_score"] == r2["severity_score"]
        assert r1["raw_flags"]["total_flags"] == r2["raw_flags"]["total_flags"]


# ── Missing data handling ─────────────────────────────────

class TestMissingData:
    def setup_method(self):
        self.engine = RedFlagEngine()

    @pytest.mark.asyncio
    async def test_all_engines_unavailable(self):
        result = await self.engine.analyze("unknown_user", {}, {}, {})
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "GitHub Data Unavailable" in flags
        assert "Profile Data Unavailable" in flags
        assert "LeetCode Data Unavailable" in flags
        assert result["severity_score"] >= 9  # 3 + 3 + 3

    @pytest.mark.asyncio
    async def test_github_only_unavailable(self):
        result = await self.engine.analyze(
            "partial_user", {}, _clean_profile(), _clean_leetcode()
        )
        flags = [f["flag"] for f in result["raw_flags"]["flags"]]
        assert "GitHub Data Unavailable" in flags
        assert "Profile Data Unavailable" not in flags

    @pytest.mark.asyncio
    async def test_interpretation_text(self):
        r1 = await self.engine.analyze(
            "u",
            _clean_github(burst_flag=True, average_contributors=0.5),
            _clean_profile(experience_ratio=0.1, project_ratio=0.1),
            _clean_leetcode(),
        )
        assert "inconsistencies" in r1["explanation"]["interpretation"].lower()
