"""GitHub Authenticity Engine — Engine 1 of ProofStack.

Analyzes a GitHub user's public repositories and commits to produce
a deterministic Trust Score based exclusively on measurable metrics.

=== METRICS COMPUTED ===

  total_repositories .... number of public repos
  total_commits ......... sum of commits across all repos
  commit_variance ....... population variance of per-repo commit counts
  burst_flag ............ True if ≥40 % of all commits fall within any 7-day window
  commit_message_entropy  Shannon entropy (bits) of the concatenated commit messages
  average_branches ...... mean branch count per repo
  average_contributors .. mean contributor count per repo
  average_repo_age_days . mean age of repos in days (from created_at to now)

=== SCORING FORMULA (explicit, no hidden weights — max 100) ===

  base = 0

  # Commit consistency — up to 20 pts
  base += min(total_commits × 0.1, 20)

  # Commit message entropy — up to 15 pts
  base += min(commit_message_entropy × 3, 15)

  # Burst penalty — flat −15 pts if burst_flag is True
  base -= 15 if burst_flag else 0

  # Repo depth — up to 15 pts
  base += min(total_repositories × 1.5, 15)

  # Repo diversity (language count) — up to 15 pts
  base += min(language_count × 3, 15)

  # Longevity factor — up to 10 pts
  base += min(average_repo_age_days / 120, 10)

  # Contribution frequency — up to 15 pts
  commits_per_repo = total_commits / max(repos_analyzed, 1)
  base += min(commits_per_repo × 0.5, 15)

  # Branching activity — up to 10 pts
  base += min(average_branches × 3, 10)

  Max positive = 20 + 15 + 15 + 15 + 10 + 15 + 10 = 100
  Min (with burst): -15 floor clamped to 0

  normalized_score = clamp(base, 0, 100)

Every number above is reproduced verbatim in the explanation dict.
"""

from __future__ import annotations

import asyncio
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.services.github_client import GitHubClient

_MAX_REPOS = 10


class GitHubAuthenticityEngine:
    """Deterministic authenticity analysis for a GitHub user."""

    def __init__(self) -> None:
        self.client = GitHubClient()

    # ── public entry point ──────────────────────────────────

    async def analyze(self, username: str, repos: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Run full analysis and return structured result dict.

        Returns:
            {
                "username": str,
                "raw_metrics": { ... },
                "normalized_score": float,
                "explanation": { ... }
            }
        """
        logger.info(f"Starting GitHub authenticity analysis for {username}")
        if repos is None:
            repos = await self.client.get_repos(username)
        logger.info(f"GitHub repos fetched successfully for {username}: {len(repos)} repos")

        if not repos:
            return self._empty_result(username)

        # Sort by recent push and limit
        sorted_repos = sorted(repos, key=lambda r: r.get("pushed_at", ""), reverse=True)[:_MAX_REPOS]

        commit_counts: List[int] = []
        commit_dates: List[datetime] = []
        commit_messages: List[str] = []
        branch_counts: List[int] = []
        contributor_counts: List[int] = []
        repo_ages: List[float] = []

        now = datetime.now(timezone.utc)

        async def _fetch_repo(repo: Dict[str, Any]) -> None:
            repo_name: str = repo["name"]

            # Repo age
            created_str: str = repo["created_at"]
            created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            repo_age_days = (now - created_at).total_seconds() / 86_400.0
            repo_ages.append(repo_age_days)

            # Fetch per-repo data concurrently
            commits_t, branches_t, contributors_t = await asyncio.gather(
                self.client.get_commits(username, repo_name),
                self.client.get_branches(username, repo_name),
                self.client.get_contributors(username, repo_name),
            )

            branch_counts.append(len(branches_t))
            contributor_counts.append(len(contributors_t))
            commit_counts.append(len(commits_t))

            for commit in commits_t:
                msg: str = commit.get("commit", {}).get("message", "")
                commit_messages.append(msg)

                date_str: str = (
                    commit.get("commit", {}).get("author", {}).get("date", "")
                )
                if date_str:
                    commit_dates.append(
                        datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    )

        # Fetch all repos concurrently (limited to _MAX_REPOS already)
        await asyncio.gather(*[_fetch_repo(repo) for repo in sorted_repos])

        # ── METRICS ─────────────────────────────────────────

        total_commits = sum(commit_counts)
        repo_count = len(repos)

        # Commit variance (population)
        variance = (
            statistics.pvariance(commit_counts) if len(commit_counts) > 1 else 0.0
        )

        # Burst detection — ≥40 % of commits within any 7-day window
        burst_flag = self._detect_commit_burst(commit_dates, threshold_pct=0.40)

        # Commit-message Shannon entropy (bits)
        entropy_score = self._commit_message_entropy(commit_messages)

        # Averages (safe against zero-length)
        avg_branches = (
            sum(branch_counts) / len(branch_counts) if branch_counts else 0.0
        )
        avg_contributors = (
            sum(contributor_counts) / len(contributor_counts)
            if contributor_counts
            else 0.0
        )
        avg_repo_age = (
            sum(repo_ages) / len(repo_ages) if repo_ages else 0.0
        )

        # ── Monthly commit aggregation (real data for charts) ──
        monthly_commits = self._aggregate_monthly_commits(commit_dates)

        # ── Per-repo details (real data for charts) ──
        repo_details = [
            {
                "name": sorted_repos[i]["name"],
                "commits": commit_counts[i],
                "language": sorted_repos[i].get("language", "Unknown"),
            }
            for i in range(len(sorted_repos))
        ]

        raw_metrics: Dict[str, Any] = {
            "total_repositories": repo_count,
            "repos_analyzed": len(sorted_repos),
            "total_commits": total_commits,
            "commit_variance": round(variance, 4),
            "burst_flag": burst_flag,
            "commit_message_entropy": round(entropy_score, 4),
            "average_branches": round(avg_branches, 4),
            "average_contributors": round(avg_contributors, 4),
            "average_repo_age_days": round(avg_repo_age, 2),
            "language_count": len(set(
                r.get("language", "").lower()
                for r in repos
                if r.get("language")
            )),
            "monthly_commits": monthly_commits,
            "repo_details": repo_details,
        }

        normalized_score = self._calculate_score(raw_metrics)

        explanation = self._build_explanation(raw_metrics, normalized_score)

        return {
            "username": username,
            "raw_metrics": raw_metrics,
            "normalized_score": normalized_score,
            "explanation": explanation,
        }

    # ── monthly aggregation for real chart data ───────────

    @staticmethod
    def _aggregate_monthly_commits(dates: List[datetime]) -> List[Dict[str, Any]]:
        """Aggregate commit dates into monthly buckets (YYYY-MM format).

        Returns a chronologically sorted list of {date, count} dicts
        with real data — no synthesis, no randomness.
        """
        if not dates:
            return []

        buckets: Dict[str, int] = defaultdict(int)
        for dt in dates:
            key = dt.strftime("%Y-%m")
            buckets[key] += 1

        return [
            {"date": month, "count": count}
            for month, count in sorted(buckets.items())
        ]

    # ── deterministic scoring ───────────────────────────────

    def _calculate_score(self, metrics: Dict[str, Any]) -> float:
        """Apply the explicit scoring formula documented in the module docstring.

        Max positive = 20 + 15 + 15 + 15 + 10 + 15 + 10 = 100.
        Burst penalty = -15.
        """
        score = 0.0

        # Commit consistency — up to 20 pts
        commit_pts = min(metrics["total_commits"] * 0.1, 20)
        score += commit_pts

        # Entropy quality — up to 15 pts
        entropy_pts = min(metrics["commit_message_entropy"] * 3, 15)
        score += entropy_pts

        # Burst penalty — flat −15
        burst_penalty = 15.0 if metrics["burst_flag"] else 0.0
        score -= burst_penalty

        # Repo depth — up to 15 pts
        repo_pts = min(metrics["total_repositories"] * 1.5, 15)
        score += repo_pts

        # Repo diversity (language count) — up to 15 pts
        diversity_pts = min(metrics.get("language_count", 0) * 3, 15)
        score += diversity_pts

        # Longevity factor — up to 10 pts
        longevity_pts = min(metrics["average_repo_age_days"] / 120.0, 10)
        score += longevity_pts

        # Contribution frequency — up to 15 pts
        repos_analyzed = max(metrics.get("repos_analyzed", 1), 1)
        commits_per_repo = metrics["total_commits"] / repos_analyzed
        frequency_pts = min(commits_per_repo * 0.5, 15)
        score += frequency_pts

        # Branching activity — up to 10 pts
        branch_pts = min(metrics["average_branches"] * 3, 10)
        score += branch_pts

        return round(max(0.0, min(score, 100.0)), 2)

    # ── entropy calculation ─────────────────────────────────

    @staticmethod
    def _commit_message_entropy(messages: List[str]) -> float:
        """Shannon entropy (bits) of the character distribution across all messages.

        Higher entropy indicates more varied/meaningful commit messages.
        Typical range for English text: 3.5–4.5 bits.
        """
        text = " ".join(messages)
        if not text:
            return 0.0

        counts = Counter(text)
        total = sum(counts.values())
        entropy = -sum(
            (count / total) * math.log2(count / total)
            for count in counts.values()
            if count > 0
        )
        return entropy

    # ── burst detection ─────────────────────────────────────

    @staticmethod
    def _detect_commit_burst(
        dates: List[datetime],
        threshold_pct: float = 0.40,
        window_days: int = 7,
    ) -> bool:
        """Return True if ≥ threshold_pct of all commits fall within any
        *window_days*-day sliding window.

        Algorithm:
          1. Sort dates chronologically.
          2. Use a two-pointer sliding window of *window_days* days.
          3. Track the maximum number of commits in any window.
          4. Flag if max_window_count / total ≥ threshold_pct.

        This is O(n) after the sort and fully deterministic.
        """
        if not dates:
            return False

        total = len(dates)
        if total <= 2:
            return False

        sorted_dates = sorted(dates)
        from datetime import timedelta

        window = timedelta(days=window_days)
        max_in_window = 0
        left = 0

        for right in range(total):
            while sorted_dates[right] - sorted_dates[left] > window:
                left += 1
            window_count = right - left + 1
            if window_count > max_in_window:
                max_in_window = window_count

        return (max_in_window / total) >= threshold_pct

    # ── explanation builder ─────────────────────────────────

    @staticmethod
    def _build_explanation(
        metrics: Dict[str, Any], score: float
    ) -> Dict[str, Any]:
        """Produce a fully deterministic explanation dict.

        Every value maps to a measurable threshold — no vague statements.
        """
        commit_pts = min(metrics["total_commits"] * 0.1, 20)
        entropy_pts = min(metrics["commit_message_entropy"] * 3, 15)
        burst_penalty = 15.0 if metrics["burst_flag"] else 0.0
        repo_pts = min(metrics["total_repositories"] * 1.5, 15)
        diversity_pts = min(metrics.get("language_count", 0) * 3, 15)
        longevity_pts = min(metrics["average_repo_age_days"] / 120.0, 10)
        repos_analyzed = max(metrics.get("repos_analyzed", 1), 1)
        commits_per_repo = metrics["total_commits"] / repos_analyzed
        frequency_pts = min(commits_per_repo * 0.5, 15)
        branch_pts = min(metrics["average_branches"] * 3, 10)

        return {
            "formula": (
                "score = commit_pts + entropy_pts - burst_penalty "
                "+ repo_pts + diversity_pts + longevity_pts "
                "+ frequency_pts + branch_pts"
            ),
            "components": {
                "commit_pts": {
                    "value": round(commit_pts, 2),
                    "formula": "min(total_commits × 0.1, 20)",
                    "input": metrics["total_commits"],
                },
                "entropy_pts": {
                    "value": round(entropy_pts, 2),
                    "formula": "min(commit_message_entropy × 3, 15)",
                    "input": round(metrics["commit_message_entropy"], 4),
                },
                "burst_penalty": {
                    "value": burst_penalty,
                    "formula": "15 if burst_flag else 0",
                    "input": metrics["burst_flag"],
                },
                "repo_pts": {
                    "value": round(repo_pts, 2),
                    "formula": "min(total_repositories × 1.5, 15)",
                    "input": metrics["total_repositories"],
                },
                "diversity_pts": {
                    "value": round(diversity_pts, 2),
                    "formula": "min(language_count × 3, 15)",
                    "input": metrics.get("language_count", 0),
                },
                "longevity_pts": {
                    "value": round(longevity_pts, 2),
                    "formula": "min(average_repo_age_days / 120, 10)",
                    "input": round(metrics["average_repo_age_days"], 2),
                },
                "frequency_pts": {
                    "value": round(frequency_pts, 2),
                    "formula": "min(commits_per_repo × 0.5, 15)",
                    "input": round(commits_per_repo, 2),
                },
                "branch_pts": {
                    "value": round(branch_pts, 2),
                    "formula": "min(average_branches × 3, 10)",
                    "input": round(metrics["average_branches"], 4),
                },
            },
            "final_score": score,
            "burst_detected": metrics["burst_flag"],
            "entropy_quality": (
                "high" if metrics["commit_message_entropy"] > 3.5 else "moderate"
            ),
            "collaboration_signal": metrics["average_contributors"] > 1.0,
        }

    # ── empty fallback ──────────────────────────────────────

    @staticmethod
    def _empty_result(username: str) -> Dict[str, Any]:
        return {
            "username": username,
            "raw_metrics": {
                "total_repositories": 0,
                "repos_analyzed": 0,
                "total_commits": 0,
                "commit_variance": 0.0,
                "burst_flag": False,
                "commit_message_entropy": 0.0,
                "average_branches": 0.0,
                "average_contributors": 0.0,
                "average_repo_age_days": 0.0,
                "language_count": 0,
            },
            "normalized_score": 0.0,
            "explanation": {
                "formula": "N/A — no public repositories found",
                "components": {},
                "final_score": 0.0,
                "burst_detected": False,
                "entropy_quality": "none",
                "collaboration_signal": False,
            },
        }
