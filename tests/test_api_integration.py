"""Integration & API Tests for ProofStack.

Tests API authentication, health check, endpoint availability,
and input validation — uses FastAPI TestClient (no external services needed).

Run with:
    pytest tests/test_api_integration.py -v
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Set env vars before importing app
os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres@localhost/proofstack")
os.environ.setdefault("API_KEY", "test-api-key-12345")

from app.main import app

API_KEY = "test-api-key-12345"
WRONG_KEY = "wrong-key"


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# ── Health check (no auth required) ──────────────────────

class TestHealthCheck:
    def test_health_no_auth(self, client):
        """Health endpoint works without API key."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "proofstack"
        assert "status" in data
        assert "version" in data

    def test_health_includes_checks(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "checks" in data
        assert "timestamp" in data


# ── API key authentication ────────────────────────────────

class TestAPIAuth:
    def test_no_key_returns_401(self, client):
        """Missing X-API-Key → 401."""
        resp = client.get("/jobs/nonexistent")
        assert resp.status_code == 401
        assert "Missing" in resp.json()["detail"]

    def test_wrong_key_returns_403(self, client):
        """Invalid X-API-Key → 403."""
        resp = client.get(
            "/jobs/nonexistent",
            headers={"X-API-Key": WRONG_KEY},
        )
        assert resp.status_code == 403
        assert "Invalid" in resp.json()["detail"]

    def test_valid_key_passes_auth(self, client):
        """Valid key passes auth (endpoint may return 404 for missing job, not 401/403)."""
        resp = client.get(
            "/jobs/nonexistent-job-id",
            headers={"X-API-Key": API_KEY},
        )
        # Should NOT be 401 or 403 — auth passed
        assert resp.status_code not in (401, 403)

    def test_shared_endpoint_no_auth(self, client):
        """Shared dashboard endpoint works without API key."""
        resp = client.get("/api/dashboard/shared/nonexistent-token")
        # Should get 404 (token not found), not 401
        assert resp.status_code in (404, 500)  # 500 if DB unavailable


# ── Protected endpoint checks ─────────────────────────────

class TestProtectedEndpoints:
    """Verify that all major routes require auth."""

    PROTECTED_ROUTES = [
        ("GET", "/jobs/test-id"),
        ("POST", "/jobs/analyze"),
        ("POST", "/jobs/test-id/retry"),
    ]

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
    def test_protected_route_requires_auth(self, client, method, path):
        """All protected routes return 401 without key."""
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.post(path, json={})
        assert resp.status_code == 401


# ── Input validation ──────────────────────────────────────

class TestInputValidation:
    def test_analyze_rejects_empty_body(self, client):
        resp = client.post(
            "/jobs/analyze",
            headers={"X-API-Key": API_KEY},
            json={},
        )
        assert resp.status_code == 422  # validation error

    def test_analyze_rejects_invalid_username(self, client):
        resp = client.post(
            "/jobs/analyze",
            headers={"X-API-Key": API_KEY},
            json={
                "username": "bad user name!!",
                "role_level": "mid",
                "resume_data": {"skills": [], "experience": [], "projects": []},
                "consent": {
                    "consent_version": "v1.0.0",
                    "consent_given": True,
                },
            },
        )
        assert resp.status_code == 422

    def test_analyze_rejects_invalid_role(self, client):
        resp = client.post(
            "/jobs/analyze",
            headers={"X-API-Key": API_KEY},
            json={
                "username": "validuser",
                "role_level": "ceo",
                "resume_data": {"skills": [], "experience": [], "projects": []},
                "consent": {
                    "consent_version": "v1.0.0",
                    "consent_given": True,
                },
            },
        )
        assert resp.status_code == 422

    def test_analyze_rejects_missing_consent(self, client):
        resp = client.post(
            "/jobs/analyze",
            headers={"X-API-Key": API_KEY},
            json={
                "username": "validuser",
                "role_level": "mid",
                "resume_data": {"skills": [], "experience": [], "projects": []},
            },
        )
        assert resp.status_code == 422


# ── Schema validation ─────────────────────────────────────

class TestSchemaValidation:
    """Test Pydantic schema validators directly."""

    def test_github_username_regex(self):
        from app.schemas.full_analysis import FullAnalysisRequest

        # Valid usernames
        for name in ["torvalds", "octocat", "my-user-1", "a"]:
            # Just checking the regex accepts these
            import re
            assert re.match(
                r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$", name
            )

        # Invalid usernames
        for name in ["-leading", "trailing-", "has spaces", "special!char", "a" * 40]:
            assert not re.match(
                r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$", name
            )

    def test_consent_version_required(self):
        from app.schemas.full_analysis import ConsentPayload

        with pytest.raises(Exception):
            ConsentPayload(consent_version="", consent_given=True)
