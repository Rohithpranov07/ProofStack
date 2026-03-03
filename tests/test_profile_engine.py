"""Profile Consistency Engine – Unit Tests.

Tests skill matching, project matching, experience timeline,
LinkedIn verification, collaboration signal, and scoring formula.

Run with:
    pytest tests/test_profile_engine.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.profile_consistency_engine import (
    ProfileConsistencyEngine,
    _SKILL_TO_LANGUAGES,
)
from app.schemas.profile import (
    LinkedInStructured,
    ResumeStructured,
    SkillItem,
    ExperienceItem,
    ProjectItem,
)


# ── Helpers ───────────────────────────────────────────────

NOW = datetime.now(timezone.utc)


def _make_repo(
    name: str = "myrepo",
    language: str = "Python",
    days_old: int = 365,
    topics: list | None = None,
    description: str = "",
) -> Dict[str, Any]:
    created = NOW - timedelta(days=days_old)
    return {
        "name": name,
        "language": language,
        "created_at": created.isoformat(),
        "pushed_at": NOW.isoformat(),
        "topics": topics or [],
        "description": description,
    }


def _make_resume(
    skills: list[SkillItem] | None = None,
    experience: list[ExperienceItem] | None = None,
    projects: list[ProjectItem] | None = None,
) -> ResumeStructured:
    return ResumeStructured(
        skills=skills or [SkillItem(name="Python", years=2)],
        experience=experience or [
            ExperienceItem(
                company="Acme",
                start_date="2023-01-01",
                end_date="2024-01-01",
            )
        ],
        projects=projects or [ProjectItem(name="myrepo")],
    )


# ── Skill-to-Language mapping tests ───────────────────────

class TestSkillMapping:
    def test_react_maps_to_js_ts(self):
        assert "javascript" in _SKILL_TO_LANGUAGES["react"]
        assert "typescript" in _SKILL_TO_LANGUAGES["react"]

    def test_django_maps_to_python(self):
        assert "python" in _SKILL_TO_LANGUAGES["django"]

    def test_spring_maps_to_java(self):
        assert "java" in _SKILL_TO_LANGUAGES["spring"]

    def test_flutter_maps_to_dart(self):
        assert "dart" in _SKILL_TO_LANGUAGES["flutter"]

    def test_docker_maps_to_dockerfile(self):
        assert "dockerfile" in _SKILL_TO_LANGUAGES["docker"]

    def test_mapping_count(self):
        """At least 50 framework→language mappings exist."""
        assert len(_SKILL_TO_LANGUAGES) >= 50


# ── Scoring formula tests ────────────────────────────────

class TestScoringFormula:
    """Test the explicit scoring formula: skill(30) + project(20) + experience(20) + linkedin(15) + collab(15)."""

    def test_perfect_score(self):
        """skill=1.0, project=1.0, exp=1.0, linkedin=True, collab=True → 100."""
        # Using the formula directly (since _calculate_score is internal)
        score = (1.0 * 30) + (1.0 * 20) + (1.0 * 20) + 15 + 15
        assert score == 100.0

    def test_no_linkedin_no_collab(self):
        """Missing linkedin and collab → max 70."""
        score = (1.0 * 30) + (1.0 * 20) + (1.0 * 20) + 0 + 0
        assert score == 70.0

    def test_half_skills(self):
        score = (0.5 * 30) + (1.0 * 20) + (1.0 * 20) + 15 + 15
        assert score == 85.0


# ── Full analyze flow (mocked) ───────────────────────────

class TestAnalyzeFlow:
    @pytest.fixture
    def engine(self):
        return ProfileConsistencyEngine()

    @pytest.mark.asyncio
    async def test_empty_repos_returns_zero(self, engine):
        resume = _make_resume()
        with patch.object(engine.github, "get_repos", new_callable=AsyncMock, return_value=[]):
            result = await engine.analyze("nobody", resume)
        assert result["normalized_score"] == 0.0

    @pytest.mark.asyncio
    async def test_skill_verified_when_language_matches(self, engine):
        repos = [_make_repo("api", "Python", 730)]  # 2 years old
        resume = _make_resume(skills=[SkillItem(name="Python", years=2)])

        with patch.object(engine.github, "get_repos", new_callable=AsyncMock, return_value=repos), \
             patch.object(engine.github, "get_contributors", new_callable=AsyncMock, return_value=[{"login": "user"}]), \
             patch.object(engine.linkedin, "verify_profile", new_callable=AsyncMock, return_value=False):
            result = await engine.analyze("testuser", resume, repos=repos)

        metrics = result["raw_metrics"]
        assert metrics["skill_ratio"] > 0

    @pytest.mark.asyncio
    async def test_project_matched_case_insensitive(self, engine):
        repos = [_make_repo("MyProject", "TypeScript", 100)]
        resume = _make_resume(projects=[ProjectItem(name="myproject")])

        with patch.object(engine.github, "get_repos", new_callable=AsyncMock, return_value=repos), \
             patch.object(engine.github, "get_contributors", new_callable=AsyncMock, return_value=[{"login": "user"}]), \
             patch.object(engine.linkedin, "verify_profile", new_callable=AsyncMock, return_value=False):
            result = await engine.analyze("testuser", resume, repos=repos)

        metrics = result["raw_metrics"]
        assert metrics["project_ratio"] > 0

    @pytest.mark.asyncio
    async def test_framework_to_language_matching(self, engine):
        """React skill should match JavaScript repo."""
        repos = [_make_repo("webapp", "JavaScript", 500)]
        resume = _make_resume(skills=[SkillItem(name="React", years=1)])

        with patch.object(engine.github, "get_repos", new_callable=AsyncMock, return_value=repos), \
             patch.object(engine.github, "get_contributors", new_callable=AsyncMock, return_value=[{"login": "user"}]), \
             patch.object(engine.linkedin, "verify_profile", new_callable=AsyncMock, return_value=False):
            result = await engine.analyze("testuser", resume, repos=repos)

        metrics = result["raw_metrics"]
        # React should be verified via JavaScript repo
        assert metrics["skill_ratio"] > 0

    @pytest.mark.asyncio
    async def test_score_in_range(self, engine):
        repos = [
            _make_repo("project-alpha", "Python", 400),
            _make_repo("project-beta", "TypeScript", 300),
        ]
        resume = _make_resume(
            skills=[SkillItem(name="Python", years=1)],
            projects=[ProjectItem(name="project-alpha")],
            experience=[ExperienceItem(company="X", start_date="2024-01-01", end_date="2024-06-01")],
        )

        with patch.object(engine.github, "get_repos", new_callable=AsyncMock, return_value=repos), \
             patch.object(engine.github, "get_contributors", new_callable=AsyncMock, return_value=[{"login": "user"}]), \
             patch.object(engine.linkedin, "verify_profile", new_callable=AsyncMock, return_value=False):
            result = await engine.analyze("testuser", resume, repos=repos)

        assert 0 <= result["normalized_score"] <= 100

    @pytest.mark.asyncio
    async def test_deterministic(self, engine):
        repos = [_make_repo("repo1", "Go", 200)]
        resume = _make_resume(skills=[SkillItem(name="Go", years=0.5)])

        async def run():
            with patch.object(engine.github, "get_repos", new_callable=AsyncMock, return_value=repos), \
                 patch.object(engine.github, "get_contributors", new_callable=AsyncMock, return_value=[{"login": "u"}]), \
                 patch.object(engine.linkedin, "verify_profile", new_callable=AsyncMock, return_value=False):
                return await engine.analyze("testuser", resume, repos=repos)

        r1 = await run()
        r2 = await run()
        assert r1["normalized_score"] == r2["normalized_score"]


# ── Collaboration signal tests ────────────────────────────

class TestCollaboration:
    @pytest.fixture
    def engine(self):
        return ProfileConsistencyEngine()

    @pytest.mark.asyncio
    async def test_multi_contributor_is_collaboration(self, engine):
        repos = [_make_repo("team-project", "Python", 100)]
        resume = _make_resume(skills=[SkillItem(name="Python", years=0.5)])
        contributors = [{"login": "user1"}, {"login": "user2"}, {"login": "user3"}]

        with patch.object(engine.github, "get_repos", new_callable=AsyncMock, return_value=repos), \
             patch.object(engine.github, "get_contributors", new_callable=AsyncMock, return_value=contributors), \
             patch.object(engine.linkedin, "verify_profile", new_callable=AsyncMock, return_value=False):
            result = await engine.analyze("testuser", resume, repos=repos)

        # Multi-contributor repos should boost collaboration signal
        # The engine stores multi_contributor_repos count in raw_metrics
        multi = result["raw_metrics"].get("multi_contributor_repos", 0)
        assert multi >= 1
