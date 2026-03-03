"""ENGINE 5 — Product Mindset Detector.

Analyzes GitHub repository README content, deployment evidence,
project originality, and maintenance recency to assess whether
a candidate builds production-quality, purpose-driven software.

=== SCORING DIMENSIONS (total 100) ===

  Problem Articulation  (0–25)
    README contains problem statement, "why" framing, or user need.

  Impact Metrics         (0–20)
    README contains quantitative impact: %, numbers, "users", "requests", etc.

  Deployment Evidence    (0–20)
    Repo contains live demo links (vercel, netlify, heroku, custom domains)
    or deployment config (Dockerfile, CI/CD, k8s manifests).

  Originality Heuristic  (0–20)
    Penalizes tutorial-clone patterns (weather app, todo app, netflix clone,
    e-commerce template, calculator, etc.).

  Recency Maintenance    (0–15)
    Repos pushed within 90 days score higher. Dormant repos score lower.

  normalized_score = clamp(sum, 0, 100)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.services.github_client import GitHubClient

_MAX_REPOS = 10

# ── Regex patterns ──────────────────────────────────────────

_PROBLEM_PATTERNS = [
    re.compile(r"\b(solves?|addresses?|tackles?|fixes?|eliminates?)\b", re.I),
    re.compile(r"\b(problem|challenge|pain\s?point|issue|gap)\b", re.I),
    re.compile(r"\b(users?\s+(need|want|struggle|face))", re.I),
    re.compile(r"\b(motivation|why\s+i\s+built|purpose|goal)\b", re.I),
    re.compile(r"\b(designed\s+to|built\s+to|aims?\s+to|intended\s+to)\b", re.I),
]

_METRIC_PATTERNS = [
    re.compile(r"\d+\s*%", re.I),
    re.compile(r"\b\d{2,}[kKmM]?\+?\s*(users?|requests?|downloads?|stars?|installs?)\b", re.I),
    re.compile(r"\b(reduced|improved|increased|processed|handled|served)\s+\d+", re.I),
    re.compile(r"\b(latency|throughput|uptime|performance)\b", re.I),
    re.compile(r"\b(benchmark|metric|measure)\b", re.I),
]

_DEPLOY_PATTERNS = [
    re.compile(r"https?://[\w.-]+\.vercel\.app", re.I),
    re.compile(r"https?://[\w.-]+\.netlify\.app", re.I),
    re.compile(r"https?://[\w.-]+\.herokuapp\.com", re.I),
    re.compile(r"https?://[\w.-]+\.railway\.app", re.I),
    re.compile(r"https?://[\w.-]+\.fly\.dev", re.I),
    re.compile(r"https?://[\w.-]+\.render\.com", re.I),
    re.compile(r"\b(live\s+demo|demo\s+link|hosted\s+at|deployed\s+(at|to|on))\b", re.I),
    re.compile(r"\b(docker|Dockerfile|docker-compose)\b"),
    re.compile(r"\b(CI/CD|GitHub\s+Actions|\.github/workflows)\b", re.I),
    re.compile(r"\b(Kubernetes|k8s|helm)\b", re.I),
]

_TUTORIAL_CLONE_PATTERNS = [
    re.compile(r"\b(weather\s+app|todo\s+(app|list)|calculator)\b", re.I),
    re.compile(r"\b(netflix\s+clone|spotify\s+clone|twitter\s+clone|instagram\s+clone)\b", re.I),
    re.compile(r"\b(e-?commerce\s+(template|starter|demo))\b", re.I),
    re.compile(r"\b(tic\s+tac\s+toe|snake\s+game|hangman)\b", re.I),
    re.compile(r"\b(crud\s+app|blog\s+(app|starter|template))\b", re.I),
    re.compile(r"\b(tutorial|sample\s+project|demo\s+project|starter\s+kit)\b", re.I),
    re.compile(r"\b(boilerplate|scaffold|template\s+repo)\b", re.I),
]


class ProductMindsetEngine:
    """Deterministic product-mindset analysis for a GitHub user's repositories."""

    def __init__(self) -> None:
        self._client = GitHubClient()

    async def analyze(
        self,
        username: str,
        *,
        repos: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run product-mindset analysis across top repos.

        Args:
            username: GitHub username.
            repos: Pre-fetched repos list. Fetches internally if None.

        Returns:
            {
                "username": str,
                "raw_metrics": { ... },
                "normalized_score": float,
                "explanation": { ... }
            }
        """
        logger.info(f"Starting product mindset analysis for {username}")

        if repos is None:
            repos = await self._client.get_repos(username)

        if not repos:
            return self._empty(username)

        # Sort by stars, then by recency — prioritise most visible repos
        sorted_repos = sorted(
            repos,
            key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at", "")),
            reverse=True,
        )[:_MAX_REPOS]

        now = datetime.now(timezone.utc)

        # Accumulators
        problem_hits: int = 0
        metric_hits: int = 0
        deploy_hits: int = 0
        tutorial_hits: int = 0
        recent_repos: int = 0
        repo_details: List[Dict[str, Any]] = []

        for repo in sorted_repos:
            readme_text = await self._fetch_readme(username, repo["name"])
            pushed_str = repo.get("pushed_at", "")
            desc = repo.get("description") or ""
            combined_text = f"{desc}\n{readme_text}"

            # Problem articulation
            has_problem = any(p.search(combined_text) for p in _PROBLEM_PATTERNS)
            if has_problem:
                problem_hits += 1

            # Impact metrics
            has_metrics = any(p.search(combined_text) for p in _METRIC_PATTERNS)
            if has_metrics:
                metric_hits += 1

            # Deployment evidence
            has_deploy = any(p.search(combined_text) for p in _DEPLOY_PATTERNS)
            if has_deploy:
                deploy_hits += 1

            # Tutorial clone detection
            is_tutorial = any(p.search(combined_text) for p in _TUTORIAL_CLONE_PATTERNS)
            name_is_tutorial = any(p.search(repo["name"]) for p in _TUTORIAL_CLONE_PATTERNS)
            if is_tutorial or name_is_tutorial:
                tutorial_hits += 1

            # Recency
            is_recent = False
            if pushed_str:
                pushed_at = datetime.fromisoformat(pushed_str.replace("Z", "+00:00"))
                days_since_push = (now - pushed_at).total_seconds() / 86_400.0
                is_recent = days_since_push <= 90
                if is_recent:
                    recent_repos += 1

            repo_details.append({
                "repo": repo["name"],
                "has_problem_statement": has_problem,
                "has_impact_metrics": has_metrics,
                "has_deployment": has_deploy,
                "is_tutorial_clone": is_tutorial or name_is_tutorial,
                "is_recent": is_recent,
            })

        total = len(sorted_repos)

        # ── Score components ────────────────────────────────

        # Problem articulation: 0–25
        problem_ratio = problem_hits / total
        problem_score = round(min(problem_ratio * 2.0, 1.0) * 25.0, 2)

        # Impact metrics: 0–20
        metric_ratio = metric_hits / total
        metric_score = round(min(metric_ratio * 2.5, 1.0) * 20.0, 2)

        # Deployment: 0–20
        deploy_ratio = deploy_hits / total
        deploy_score = round(min(deploy_ratio * 2.5, 1.0) * 20.0, 2)

        # Originality: 0–20 (inverted — more tutorials = lower score)
        tutorial_ratio = tutorial_hits / total
        originality_factor = max(0.0, 1.0 - tutorial_ratio * 1.5)
        originality_score = round(originality_factor * 20.0, 2)

        # Recency: 0–15
        recency_ratio = recent_repos / total
        recency_score = round(min(recency_ratio * 1.5, 1.0) * 15.0, 2)

        total_score = round(
            max(0.0, min(
                problem_score + metric_score + deploy_score + originality_score + recency_score,
                100.0,
            )),
            2,
        )

        raw_metrics: Dict[str, Any] = {
            "repos_analyzed": total,
            "problem_hits": problem_hits,
            "metric_hits": metric_hits,
            "deploy_hits": deploy_hits,
            "tutorial_hits": tutorial_hits,
            "recent_repos": recent_repos,
            "problem_ratio": round(problem_ratio, 4),
            "metric_ratio": round(metric_ratio, 4),
            "deploy_ratio": round(deploy_ratio, 4),
            "tutorial_ratio": round(tutorial_ratio, 4),
            "recency_ratio": round(recency_ratio, 4),
            "repo_details": repo_details,
        }

        explanation: Dict[str, Any] = {
            "formula": (
                "problem(ratio*2, max 25) + metrics(ratio*2.5, max 20) "
                "+ deploy(ratio*2.5, max 20) + originality(1 - tutorial*1.5, max 20) "
                "+ recency(ratio*1.5, max 15)"
            ),
            "components": {
                "problem_articulation": {"value": problem_score, "max": 25},
                "impact_metrics": {"value": metric_score, "max": 20},
                "deployment_evidence": {"value": deploy_score, "max": 20},
                "originality": {"value": originality_score, "max": 20},
                "recency_maintenance": {"value": recency_score, "max": 15},
            },
            "final_score": total_score,
            "tutorial_clone_ratio": round(tutorial_ratio, 4),
        }

        return {
            "username": username,
            "raw_metrics": raw_metrics,
            "normalized_score": total_score,
            "explanation": explanation,
        }

    # ── README fetcher ──────────────────────────────────────

    async def _fetch_readme(self, username: str, repo_name: str) -> str:
        """Fetch raw README content. Returns empty string on failure."""
        try:
            import httpx
            url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
            from app.core.config import settings
            headers = {
                "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
                "Accept": "application/vnd.github.raw+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text[:10_000]  # Cap to prevent memory issues
                return ""
        except Exception:
            return ""

    # ── empty fallback ──────────────────────────────────────

    @staticmethod
    def _empty(username: str) -> Dict[str, Any]:
        return {
            "username": username,
            "raw_metrics": {
                "repos_analyzed": 0,
                "problem_hits": 0,
                "metric_hits": 0,
                "deploy_hits": 0,
                "tutorial_hits": 0,
                "recent_repos": 0,
                "problem_ratio": 0.0,
                "metric_ratio": 0.0,
                "deploy_ratio": 0.0,
                "tutorial_ratio": 0.0,
                "recency_ratio": 0.0,
                "repo_details": [],
            },
            "normalized_score": 0.0,
            "explanation": {
                "formula": "N/A — no public repositories found",
                "components": {},
                "final_score": 0.0,
                "tutorial_clone_ratio": 0.0,
            },
        }
