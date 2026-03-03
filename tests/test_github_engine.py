"""GitHub Authenticity Engine – Unit Tests.

Tests the deterministic scoring, entropy calculation, burst detection,
and monthly aggregation logic — no network calls.

Run with:
    pytest tests/test_github_engine.py -v
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from app.services.github_auth_engine import GitHubAuthenticityEngine


# ── Fixtures ──────────────────────────────────────────────

def _make_repo(
    name: str = "repo",
    language: str = "Python",
    days_old: int = 365,
    pushed_at: str | None = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    created = now - timedelta(days=days_old)
    pushed = pushed_at or now.isoformat()
    return {
        "name": name,
        "language": language,
        "created_at": created.isoformat(),
        "pushed_at": pushed,
    }


def _make_commit(
    message: str = "fix: update logic",
    date: datetime | None = None,
) -> Dict[str, Any]:
    d = date or datetime.now(timezone.utc)
    return {
        "commit": {
            "message": message,
            "author": {"date": d.isoformat()},
        }
    }


# ── Scoring formula tests ────────────────────────────────

class TestScoring:
    """Verify the explicit scoring formula from the module docstring."""

    def setup_method(self):
        self.engine = GitHubAuthenticityEngine()

    def test_score_zero_when_all_zero(self):
        metrics = {
            "total_commits": 0,
            "commit_message_entropy": 0.0,
            "burst_flag": False,
            "total_repositories": 0,
            "language_count": 0,
            "average_repo_age_days": 0.0,
            "repos_analyzed": 1,
            "average_branches": 0.0,
        }
        assert self.engine._calculate_score(metrics) == 0.0

    def test_score_max_100(self):
        metrics = {
            "total_commits": 999,
            "commit_message_entropy": 5.0,
            "burst_flag": False,
            "total_repositories": 20,
            "language_count": 10,
            "average_repo_age_days": 3000,
            "repos_analyzed": 5,
            "average_branches": 10.0,
        }
        assert self.engine._calculate_score(metrics) == 100.0

    def test_score_never_negative(self):
        metrics = {
            "total_commits": 1,
            "commit_message_entropy": 0.0,
            "burst_flag": True,  # -15 penalty
            "total_repositories": 1,
            "language_count": 0,
            "average_repo_age_days": 0.0,
            "repos_analyzed": 1,
            "average_branches": 0.0,
        }
        score = self.engine._calculate_score(metrics)
        assert score >= 0.0

    def test_burst_penalty_applied(self):
        base = {
            "total_commits": 100,
            "commit_message_entropy": 4.0,
            "total_repositories": 5,
            "language_count": 3,
            "average_repo_age_days": 365,
            "repos_analyzed": 5,
            "average_branches": 2.0,
        }
        no_burst = {**base, "burst_flag": False}
        with_burst = {**base, "burst_flag": True}

        score_no = self.engine._calculate_score(no_burst)
        score_yes = self.engine._calculate_score(with_burst)
        assert score_no - score_yes == pytest.approx(15.0, abs=0.1)

    def test_commit_points_capped_at_20(self):
        metrics = {
            "total_commits": 500,
            "commit_message_entropy": 0.0,
            "burst_flag": False,
            "total_repositories": 0,
            "language_count": 0,
            "average_repo_age_days": 0.0,
            "repos_analyzed": 1,
            "average_branches": 0.0,
        }
        # 500 * 0.1 = 50 → capped at 20
        # plus frequency: min(500/1 * 0.5, 15) = 15
        score = self.engine._calculate_score(metrics)
        assert score == 35.0  # 20 + 15

    def test_deterministic_same_input(self):
        metrics = {
            "total_commits": 50,
            "commit_message_entropy": 3.8,
            "burst_flag": False,
            "total_repositories": 8,
            "language_count": 4,
            "average_repo_age_days": 200,
            "repos_analyzed": 8,
            "average_branches": 1.5,
        }
        s1 = self.engine._calculate_score(metrics)
        s2 = self.engine._calculate_score(metrics)
        assert s1 == s2

    def test_score_components_add_up(self):
        """Verify explanation components sum to the final score."""
        metrics = {
            "total_commits": 80,
            "commit_message_entropy": 3.5,
            "burst_flag": False,
            "total_repositories": 6,
            "language_count": 3,
            "average_repo_age_days": 300,
            "repos_analyzed": 6,
            "average_branches": 2.0,
            "average_contributors": 1.5,
        }
        score = self.engine._calculate_score(metrics)
        explanation = self.engine._build_explanation(metrics, score)
        components = explanation["components"]
        total = sum(
            c["value"] for name, c in components.items() if name != "burst_penalty"
        ) - components["burst_penalty"]["value"]
        assert round(max(0, min(total, 100)), 2) == score


# ── Entropy tests ─────────────────────────────────────────

class TestEntropy:
    def test_empty_messages(self):
        assert GitHubAuthenticityEngine._commit_message_entropy([]) == 0.0

    def test_single_char_repeated(self):
        # All same character → entropy = 0
        assert GitHubAuthenticityEngine._commit_message_entropy(["aaaa"]) == 0.0

    def test_english_text_range(self):
        messages = [
            "fix: resolve null pointer in user service",
            "feat: add pagination to search results",
            "refactor: extract validation logic",
            "docs: update API reference for v2",
            "chore: bump dependencies to latest",
        ]
        entropy = GitHubAuthenticityEngine._commit_message_entropy(messages)
        # English text typically 3.5-4.5 bits
        assert 3.0 <= entropy <= 5.0

    def test_higher_for_diverse_messages(self):
        uniform = ["aaa"] * 10
        diverse = [f"commit {chr(65 + i)}: fix bug #{i}" for i in range(10)]
        e_uniform = GitHubAuthenticityEngine._commit_message_entropy(uniform)
        e_diverse = GitHubAuthenticityEngine._commit_message_entropy(diverse)
        assert e_diverse > e_uniform


# ── Burst detection tests ─────────────────────────────────

class TestBurstDetection:
    def test_empty_dates(self):
        assert GitHubAuthenticityEngine._detect_commit_burst([]) is False

    def test_few_dates_no_burst(self):
        assert GitHubAuthenticityEngine._detect_commit_burst(
            [datetime.now(timezone.utc)]
        ) is False

    def test_all_same_day_is_burst(self):
        now = datetime.now(timezone.utc)
        dates = [now] * 10  # 10 commits on same day
        assert GitHubAuthenticityEngine._detect_commit_burst(dates) is True

    def test_spread_over_year_no_burst(self):
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        dates = [base + timedelta(days=i * 30) for i in range(12)]
        assert GitHubAuthenticityEngine._detect_commit_burst(dates) is False

    def test_40_percent_threshold(self):
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # 6 spread out, 4 clustered (40% = exactly at threshold)
        spread = [base + timedelta(days=i * 30) for i in range(6)]
        cluster = [base + timedelta(days=200, hours=i) for i in range(4)]
        dates = spread + cluster
        assert GitHubAuthenticityEngine._detect_commit_burst(dates) is True

    def test_custom_threshold(self):
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        spread = [base + timedelta(days=i * 30) for i in range(8)]
        cluster = [base + timedelta(days=250, hours=i) for i in range(2)]
        dates = spread + cluster
        # 2/10 = 20%, below 40% threshold
        assert GitHubAuthenticityEngine._detect_commit_burst(dates) is False
        # But above 15% threshold
        assert GitHubAuthenticityEngine._detect_commit_burst(
            dates, threshold_pct=0.15
        ) is True


# ── Monthly aggregation tests ─────────────────────────────

class TestMonthlyAggregation:
    def test_empty(self):
        result = GitHubAuthenticityEngine._aggregate_monthly_commits([])
        assert result == []

    def test_single_month(self):
        dates = [datetime(2024, 3, d, tzinfo=timezone.utc) for d in range(1, 6)]
        result = GitHubAuthenticityEngine._aggregate_monthly_commits(dates)
        assert len(result) == 1
        assert result[0]["date"] == "2024-03"
        assert result[0]["count"] == 5

    def test_multiple_months_sorted(self):
        dates = [
            datetime(2024, 1, 15, tzinfo=timezone.utc),
            datetime(2024, 3, 10, tzinfo=timezone.utc),
            datetime(2024, 1, 20, tzinfo=timezone.utc),
            datetime(2024, 2, 5, tzinfo=timezone.utc),
        ]
        result = GitHubAuthenticityEngine._aggregate_monthly_commits(dates)
        assert len(result) == 3
        assert result[0] == {"date": "2024-01", "count": 2}
        assert result[1] == {"date": "2024-02", "count": 1}
        assert result[2] == {"date": "2024-03", "count": 1}


# ── Full analyze flow (mocked) ───────────────────────────

class TestAnalyzeFlow:
    @pytest.fixture
    def engine(self):
        return GitHubAuthenticityEngine()

    @pytest.mark.asyncio
    async def test_empty_repos_returns_zero(self, engine):
        with patch.object(engine.client, "get_repos", new_callable=AsyncMock, return_value=[]):
            result = await engine.analyze("nobody")
        assert result["normalized_score"] == 0.0
        assert result["raw_metrics"]["total_commits"] == 0

    @pytest.mark.asyncio
    async def test_analyze_returns_monthly_commits(self, engine):
        repos = [_make_repo("myrepo")]
        now = datetime.now(timezone.utc)
        commits = [
            _make_commit("fix: bug", now - timedelta(days=10)),
            _make_commit("feat: new", now - timedelta(days=40)),
        ]
        with patch.object(engine.client, "get_repos", new_callable=AsyncMock, return_value=repos), \
             patch.object(engine.client, "get_commits", new_callable=AsyncMock, return_value=commits), \
             patch.object(engine.client, "get_branches", new_callable=AsyncMock, return_value=[{"name": "main"}]), \
             patch.object(engine.client, "get_contributors", new_callable=AsyncMock, return_value=[{"login": "user"}]):
            result = await engine.analyze("testuser", repos)

        assert "monthly_commits" in result["raw_metrics"]
        assert isinstance(result["raw_metrics"]["monthly_commits"], list)
        assert "repo_details" in result["raw_metrics"]
        assert result["raw_metrics"]["repo_details"][0]["name"] == "myrepo"

    @pytest.mark.asyncio
    async def test_analyze_score_in_range(self, engine):
        repos = [_make_repo(f"repo{i}", lang, 200) for i, lang in enumerate(["Python", "Go", "Rust"])]
        now = datetime.now(timezone.utc)
        commits = [_make_commit(f"commit {i}", now - timedelta(days=i * 15)) for i in range(20)]

        with patch.object(engine.client, "get_repos", new_callable=AsyncMock, return_value=repos), \
             patch.object(engine.client, "get_commits", new_callable=AsyncMock, return_value=commits), \
             patch.object(engine.client, "get_branches", new_callable=AsyncMock, return_value=[{"name": "main"}, {"name": "dev"}]), \
             patch.object(engine.client, "get_contributors", new_callable=AsyncMock, return_value=[{"login": "user"}]):
            result = await engine.analyze("testuser", repos)

        assert 0 <= result["normalized_score"] <= 100
        assert result["username"] == "testuser"
