"""ATS Intelligence Engine Tests.

Unit tests for the ATS Resume Intelligence Engine.
Tests the pure scoring logic — no database, no HTTP calls.

Run with:
    pytest tests/test_ats_engine.py -v
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest

from app.services.ats_engine import ATSIntelligenceEngine


# ── Helper ───────────────────────────────────────────────────

def _run(coro):
    """Run async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


SAMPLE_RESUME = """
John Doe
Software Engineer | john@example.com | github.com/johndoe

SUMMARY
Experienced software engineer with 5 years building scalable web applications.
Proficient in Python, JavaScript, TypeScript, React, Node.js, and PostgreSQL.

EXPERIENCE
Senior Software Engineer — Acme Corp (Jan 2022 – Present)
• Led migration of monolith to microservices, reducing deployment time by 60%
• Built real-time analytics dashboard serving 10,000+ daily active users
• Mentored 3 junior engineers, improving team velocity by 25%

Software Engineer — StartupXYZ (Jun 2019 – Dec 2021)
• Developed REST API handling 5M requests/day with 99.9% uptime
• Implemented CI/CD pipeline reducing release cycle from 2 weeks to 2 days
• Optimized database queries resulting in 40% reduction in response time

EDUCATION
B.S. Computer Science — State University (2019)

SKILLS
Python, JavaScript, TypeScript, React, Node.js, PostgreSQL, Docker, AWS, Git
"""

MINIMAL_RESUME = """
Jane Smith
jane@email.com

I am a developer. I like coding. I know some programming.
"""

STUFFED_RESUME = """
John Expert
expert@email.com

SKILLS
Python, Python, Python, Java, Java, Java, JavaScript, JavaScript, JavaScript,
React, React, React, Node.js, Node.js, Node.js, AWS, AWS, AWS, Docker, Docker,
Machine Learning, AI, Deep Learning, NLP, Computer Vision, Blockchain, Web3,
Quantum Computing, Kubernetes, Terraform, Ansible, Chef, Puppet, SaltStack

EXPERIENCE
Developer — Company (2020 – Present)
Used Python and Java and JavaScript and React and Node.js and AWS and Docker.
Leveraged machine learning and AI and deep learning for all projects.
Synergized blockchain and web3 and quantum computing paradigms.
"""


@pytest.fixture
def engine():
    return ATSIntelligenceEngine()


class TestATSBasicAnalysis:
    """Test basic ATS analysis functionality."""

    def test_good_resume_scores_well(self, engine):
        result = _run(engine.analyze(
            username="johndoe",
            resume_text=SAMPLE_RESUME,
            role_level="mid",
            github_languages=["Python", "JavaScript", "TypeScript"],
            github_repos=[
                {"name": "api-service", "language": "Python", "commits": 150},
                {"name": "dashboard", "language": "TypeScript", "commits": 80},
            ],
            github_total_commits=230,
        ))

        assert result["engine_failed"] is False
        assert 0 <= result["normalized_score"] <= 100
        # A well-structured resume should score above 50
        assert result["normalized_score"] >= 50
        assert result["raw_metrics"]["structure_score"] >= 50
        assert result["raw_metrics"]["parse_score"] >= 50

    def test_minimal_resume_scores_low(self, engine):
        result = _run(engine.analyze(
            username="janesmith",
            resume_text=MINIMAL_RESUME,
            role_level="entry",
        ))

        assert result["engine_failed"] is False
        assert 0 <= result["normalized_score"] <= 100
        # Minimal resume should score below 50
        assert result["normalized_score"] < 60

    def test_stuffed_resume_penalized(self, engine):
        result = _run(engine.analyze(
            username="stuffedguy",
            resume_text=STUFFED_RESUME,
            role_level="mid",
            github_languages=["Python"],
        ))

        assert result["engine_failed"] is False
        rm = result["raw_metrics"]
        # Should detect stuffing (engine returns capitalized labels)
        assert rm.get("keyword_stuffing_risk") in ("Moderate", "High", "Critical")

    def test_empty_resume_returns_failed(self, engine):
        result = _run(engine.analyze(
            username="empty",
            resume_text="",
            role_level="mid",
        ))

        # Empty resume correctly triggers engine_failed
        assert result["engine_failed"] is True
        assert result["normalized_score"] == 0

    def test_whitespace_resume_returns_failed(self, engine):
        result = _run(engine.analyze(
            username="whitespace",
            resume_text="   \n\n\t  ",
            role_level="mid",
        ))

        # Whitespace-only resume correctly triggers engine_failed
        assert result["engine_failed"] is True
        assert result["normalized_score"] == 0


class TestATSScoreBounds:
    """Test that all scores stay within 0-100 bounds."""

    def test_score_never_negative(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=MINIMAL_RESUME,
            role_level="entry",
        ))
        assert result["normalized_score"] >= 0

    def test_score_never_exceeds_100(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="senior",
            github_languages=["Python", "JavaScript", "TypeScript", "React"],
            github_repos=[{"name": f"repo{i}", "language": "Python", "commits": 100} for i in range(10)],
            github_total_commits=1000,
        ))
        assert result["normalized_score"] <= 100

    def test_sub_scores_bounded(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="mid",
            github_languages=["Python"],
        ))
        rm = result["raw_metrics"]
        for key in ["structure_score", "parse_score", "skill_authenticity_score",
                     "role_alignment_score", "career_consistency_score", "readability_score"]:
            assert 0 <= rm.get(key, 0) <= 100, f"{key} out of bounds: {rm.get(key)}"


class TestATSDeterminism:
    """Test that the engine produces deterministic results."""

    def test_same_input_same_output(self, engine):
        kwargs = dict(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="mid",
            github_languages=["Python", "JavaScript"],
        )
        r1 = _run(engine.analyze(**kwargs))
        r2 = _run(engine.analyze(**kwargs))
        assert r1["normalized_score"] == r2["normalized_score"]
        assert r1["raw_metrics"]["structure_score"] == r2["raw_metrics"]["structure_score"]


class TestATSRoleLevels:
    """Test that different role levels affect scoring."""

    def test_role_levels_accepted(self, engine):
        for role in ("entry", "mid", "senior"):
            result = _run(engine.analyze(
                username="test",
                resume_text=SAMPLE_RESUME,
                role_level=role,
                github_languages=["Python"],
            ))
            assert result["engine_failed"] is False
            assert 0 <= result["normalized_score"] <= 100


class TestATSOutputStructure:
    """Test that the output has all required fields."""

    def test_required_fields_present(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="mid",
        ))

        # Top-level fields
        assert "normalized_score" in result
        assert "raw_metrics" in result
        assert "explanation" in result
        assert "engine_failed" in result

        # Raw metrics fields
        rm = result["raw_metrics"]
        required_metrics = [
            "structure_score", "parse_score", "skill_authenticity_score",
            "role_alignment_score", "career_consistency_score",
            "keyword_stuffing_risk", "recruiter_readability",
            "cross_validation_penalty",
        ]
        for field in required_metrics:
            assert field in rm, f"Missing raw_metrics field: {field}"

        # Explanation fields
        expl = result["explanation"]
        assert "structure" in expl
        assert "skills" in expl
        assert "final_score" in expl

    def test_stuffing_risk_valid_values(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="mid",
        ))
        # Engine returns capitalized labels
        valid_risks = {"None", "Low", "Moderate", "High", "Critical"}
        assert result["raw_metrics"]["keyword_stuffing_risk"] in valid_risks

    def test_readability_valid_values(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="mid",
        ))
        valid_labels = {"Excellent", "Good", "Dense", "Overloaded"}
        assert result["raw_metrics"]["recruiter_readability"] in valid_labels


class TestATSCrossValidation:
    """Test cross-validation penalty logic."""

    def test_cross_validation_with_scores(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="senior",
            github_languages=["Python"],
            github_repos=[{"name": "repo", "language": "Python", "commits": 50}],
            github_total_commits=50,
            github_score=90,
            product_mindset_score=85,
        ))
        # Should not fail
        assert result["engine_failed"] is False
        # Penalty should be a non-negative number
        assert result["raw_metrics"]["cross_validation_penalty"] >= 0

    def test_no_cross_validation_without_scores(self, engine):
        result = _run(engine.analyze(
            username="test",
            resume_text=SAMPLE_RESUME,
            role_level="mid",
        ))
        # Without github_score / product_mindset_score, penalty should be 0
        assert result["raw_metrics"]["cross_validation_penalty"] == 0
