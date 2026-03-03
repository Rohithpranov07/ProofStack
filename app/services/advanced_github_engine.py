"""Advanced GitHub Intelligence Engine - Behavioral Anomaly Detection.

Analyzes commit patterns for signs of gaming, automation, or fraud.
Produces an anomaly_score (0-100) where higher = more suspicious.

Signals: LOC anomaly, interval irregularity, cross-repo overlap,
empty commits, repetitive messages.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from app.core.logging import logger
from app.services.github_client import GitHubClient

_MAX_DETAILED_COMMITS_PER_REPO = 20
_MAX_TOTAL_DETAIL_CALLS = 100
_MAX_REPOS = 5


class AdvancedGitHubEngine:
    """Deep behavioral analysis of GitHub commit patterns."""

    def __init__(self) -> None:
        self._client = GitHubClient()

    async def analyze(
        self,
        username: str,
        repos: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run advanced behavioral analysis."""
        logger.info(f"Starting advanced GitHub analysis for {username}")

        if repos is None:
            repos = await self._client.get_repos(username)

        if not repos:
            return self._empty(username)

        owned_repos = [r for r in repos if not r.get("fork", False)]
        if not owned_repos:
            owned_repos = repos[:_MAX_REPOS]
        else:
            # Sort by stars (popularity proxy) and limit
            owned_repos = sorted(owned_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:_MAX_REPOS]

        commit_timestamps: List[datetime] = []
        loc_per_commit: List[int] = []
        repo_commit_map: Dict[str, List[datetime]] = defaultdict(list)
        all_messages: List[str] = []
        empty_commit_count = 0
        detail_calls_remaining = _MAX_TOTAL_DETAIL_CALLS

        for repo in owned_repos:
            repo_name: str = repo["name"]
            commits = await self._client.get_commits(username, repo_name)

            for commit in commits:
                author = commit.get("commit", {}).get("author") or {}
                date_str = author.get("date", "")
                msg = commit.get("commit", {}).get("message", "")
                if msg:
                    all_messages.append(msg.strip())
                if not date_str:
                    continue
                ts = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                commit_timestamps.append(ts)
                repo_commit_map[repo_name].append(ts)

            detailed_shas = [c.get("sha", "") for c in commits[:_MAX_DETAILED_COMMITS_PER_REPO] if c.get("sha")]
            if detail_calls_remaining > 0 and detailed_shas:
                batch_shas = detailed_shas[:detail_calls_remaining]
                try:
                    details = await self._client.batch_get_commit_details(
                        username, repo_name, batch_shas, concurrency=10,
                    )
                    for detail in details:
                        stats = detail.get("stats", {})
                        total_changes = stats.get("additions", 0) + stats.get("deletions", 0)
                        if total_changes == 0:
                            empty_commit_count += 1
                        loc_per_commit.append(total_changes)
                    detail_calls_remaining -= len(batch_shas)
                except Exception as exc:
                    logger.warning(
                        f"batch_get_commit_details failed for {username}/{repo_name}: {exc}"
                    )

        logger.info(f"Advanced analysis data collected for {username}")

        loc_anomaly_ratio = self._loc_anomaly(loc_per_commit)
        interval_cv = self._interval_cv(commit_timestamps)
        overlap_score = self._repo_overlap(repo_commit_map)
        inspected = len(loc_per_commit)
        empty_ratio = empty_commit_count / inspected if inspected > 0 else 0.0
        repetitive_ratio = self._repetitive_messages(all_messages)

        anomaly_score = 0.0
        anomaly_score += min(loc_anomaly_ratio * 100, 25)
        if interval_cv > 2.0:
            anomaly_score += min((interval_cv - 2.0) * 10, 25)
        anomaly_score += min(overlap_score * 4, 20)
        anomaly_score += min(empty_ratio * 75, 15)
        anomaly_score += min(repetitive_ratio * 30, 15)
        anomaly_score = round(min(anomaly_score, 100.0), 2)

        raw_metrics: Dict[str, Any] = {
            "loc_anomaly_ratio": round(float(loc_anomaly_ratio), 4),
            "interval_cv": round(float(interval_cv), 4),
            "repo_overlap_score": overlap_score,
            "empty_commit_ratio": round(float(empty_ratio), 4),
            "repetitive_message_ratio": round(float(repetitive_ratio), 4),
            "total_commits_inspected": inspected,
        }

        explanation: Dict[str, Any] = {
            "loc_anomaly_detected": loc_anomaly_ratio > 0.15,
            "irregular_intervals": interval_cv > 2.0,
            "cross_repo_overlap_detected": overlap_score > 3,
            "high_empty_commits": empty_ratio > 0.2,
            "repetitive_messages": repetitive_ratio > 0.4,
        }

        return {
            "username": username,
            "raw_metrics": raw_metrics,
            "anomaly_score": anomaly_score,
            "explanation": explanation,
        }

    @staticmethod
    def _loc_anomaly(loc_values: List[int]) -> float:
        nonzero = [v for v in loc_values if v > 0]
        if len(nonzero) < 3:
            return 0.0
        arr = np.array(nonzero, dtype=np.float64)
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        if std == 0:
            return 0.0
        threshold = mean + 2 * std
        extreme = sum(1 for v in nonzero if v > threshold)
        return extreme / len(nonzero)

    @staticmethod
    def _interval_cv(timestamps: List[datetime]) -> float:
        if len(timestamps) < 3:
            return 0.0
        sorted_ts = sorted(timestamps)
        intervals = [
            (sorted_ts[i + 1] - sorted_ts[i]).total_seconds() / 86400.0
            for i in range(len(sorted_ts) - 1)
        ]
        arr = np.array(intervals, dtype=np.float64)
        mean = float(np.mean(arr))
        if mean < 0.001:
            return 0.0
        return float(np.std(arr)) / mean

    @staticmethod
    def _repo_overlap(repo_map: Dict[str, List[datetime]]) -> int:
        repos = list(repo_map.values())
        overlap = 0
        for i in range(len(repos)):
            set_i = set(t.replace(second=0, microsecond=0) for t in repos[i])
            for j in range(i + 1, len(repos)):
                set_j = set(t.replace(second=0, microsecond=0) for t in repos[j])
                if set_i & set_j:
                    overlap += 1
        return overlap

    @staticmethod
    def _repetitive_messages(messages: List[str]) -> float:
        if len(messages) < 5:
            return 0.0
        counts = Counter(msg.lower().strip() for msg in messages)
        duplicated = sum(c - 1 for c in counts.values() if c > 1)
        return duplicated / len(messages)

    @staticmethod
    def _empty(username: str) -> Dict[str, Any]:
        return {
            "username": username,
            "raw_metrics": {
                "loc_anomaly_ratio": 0.0,
                "interval_cv": 0.0,
                "repo_overlap_score": 0,
                "empty_commit_ratio": 0.0,
                "repetitive_message_ratio": 0.0,
                "total_commits_inspected": 0,
            },
            "anomaly_score": 0.0,
            "explanation": {
                "loc_anomaly_detected": False,
                "irregular_intervals": False,
                "cross_repo_overlap_detected": False,
                "high_empty_commits": False,
                "repetitive_messages": False,
            },
        }
