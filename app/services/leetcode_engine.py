"""ENGINE 3 - LeetCode Pattern Intelligence Engine.

Deterministic scoring (0-100):
  Volume:     min(sqrt(total_solved) * 2, max 30)
  Difficulty: min(medium*20 + hard*15, max 25)
  Acceptance: acceptance_rate * 15, max 15
  Recency:    recency_score * 15, max 15
  Contest:    ranking-based curve, max 15
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, Tuple

from app.core.logging import logger
from app.services.leetcode_client import LeetCodeClient


class LeetCodeEngine:
    """Pure-function engine: input metrics -> deterministic score + explanation."""

    def __init__(self) -> None:
        self._client = LeetCodeClient()

    async def analyze(self, username: str) -> Dict[str, Any]:
        """Run the full LeetCode analysis for username."""
        logger.info(f"Starting LeetCode analysis for {username}")
        data = await self._client.fetch_profile(username)

        matched_user = data.get("data", {}).get("matchedUser")
        if matched_user is None:
            return self._empty(username)

        raw_metrics = self._extract_metrics(
            matched_user,
            data.get("data", {}).get("recentSubmissionList") or [],
        )

        score, breakdown = self._score(raw_metrics)

        return {
            "username": username,
            "raw_metrics": raw_metrics,
            "normalized_score": score,
            "explanation": self._build_explanation(raw_metrics, score, breakdown),
        }

    @staticmethod
    def _extract_metrics(
        matched_user: Dict[str, Any],
        recent_submissions: list,
    ) -> Dict[str, Any]:
        ac_sub = matched_user.get("submitStats", {}).get("acSubmissionNum") or []
        counts: Dict[str, int] = {"All": 0, "Easy": 0, "Medium": 0, "Hard": 0}
        total_submissions: int = 0
        for entry in ac_sub:
            diff = entry.get("difficulty", "")
            cnt = int(entry.get("count", 0))
            subs = int(entry.get("submissions", 0))
            if diff in counts:
                counts[diff] = cnt
            if diff == "All":
                total_submissions = subs

        total_solved = counts["All"]
        easy = counts["Easy"]
        medium = counts["Medium"]
        hard = counts["Hard"]

        easy_ratio = easy / total_solved if total_solved > 0 else 0.0
        medium_ratio = medium / total_solved if total_solved > 0 else 0.0
        hard_ratio = hard / total_solved if total_solved > 0 else 0.0
        acceptance_rate = total_solved / total_submissions if total_submissions > 0 else 0.0
        ranking = int(matched_user.get("profile", {}).get("ranking") or 0)

        now_ts = int(time.time())
        ninety_days_ago = now_ts - 90 * 86400
        recent_count = sum(
            1 for s in recent_submissions
            if int(s.get("timestamp", 0)) >= ninety_days_ago
        )
        recency_score = min(recent_count / 30.0, 1.0) if recent_submissions else 0.0

        return {
            "total_solved": total_solved,
            "easy": easy,
            "medium": medium,
            "hard": hard,
            "easy_ratio": round(easy_ratio, 4),
            "medium_ratio": round(medium_ratio, 4),
            "hard_ratio": round(hard_ratio, 4),
            "acceptance_rate": round(acceptance_rate, 4),
            "ranking": ranking,
            "recent_in_90d": recent_count,
            "recency_score": round(recency_score, 4),
            "total_submissions": total_submissions,
        }

    @staticmethod
    def _score(m: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        volume = min(math.sqrt(m["total_solved"]) * 2.0, 30.0)
        difficulty = min(m["medium_ratio"] * 20.0 + m["hard_ratio"] * 15.0, 25.0)
        acceptance = min(m["acceptance_rate"] * 15.0, 15.0)
        recency = min(m["recency_score"] * 15.0, 15.0)

        ranking = m["ranking"]
        if ranking <= 0:
            contest = 0.0
        elif ranking <= 10_000:
            contest = 15.0
        elif ranking <= 50_000:
            contest = 15.0 * (1.0 - (ranking - 10_000) / 40_000)
        elif ranking <= 200_000:
            contest = 5.0 * (1.0 - (ranking - 50_000) / 150_000)
        else:
            contest = 0.0
        contest = round(max(contest, 0.0), 2)

        breakdown = {
            "volume": round(volume, 2),
            "difficulty_balance": round(difficulty, 2),
            "acceptance": round(acceptance, 2),
            "recency": round(recency, 2),
            "contest": contest,
        }

        total = round(
            max(0.0, min(volume + difficulty + acceptance + recency + contest, 100.0)),
            2,
        )
        return total, breakdown

    @staticmethod
    def _build_explanation(
        m: Dict[str, Any], score: float, breakdown: Dict[str, float],
    ) -> Dict[str, Any]:
        if m["hard_ratio"] > 0.15:
            archetype = "Advanced Problem Solver"
        elif m["medium_ratio"] > 0.4:
            archetype = "Practical Problem Solver"
        elif m["easy_ratio"] > 0.7:
            archetype = "Easy-Dominant Profile"
        else:
            archetype = "Balanced Solver"

        summary = (
            "{solved} problems solved (E:{easy} M:{med} H:{hard}), "
            "acceptance {acc:.1%}, archetype: {arch}, score: {sc}/100"
        ).format(
            solved=m["total_solved"],
            easy=m["easy"],
            med=m["medium"],
            hard=m["hard"],
            acc=m["acceptance_rate"],
            arch=archetype,
            sc=score,
        )

        return {
            "archetype": archetype,
            "score_breakdown": breakdown,
            "formula": (
                "volume(sqrt(solved)*2, max 30) + "
                "difficulty(medium*20 + hard*15, max 25) + "
                "acceptance(rate*15, max 15) + "
                "recency(score*15, max 15) + "
                "contest(ranking-based, max 15)"
            ),
            "summary": summary,
        }

    @staticmethod
    def _empty(username: str) -> Dict[str, Any]:
        return {
            "username": username,
            "raw_metrics": {},
            "normalized_score": 0.0,
            "explanation": {
                "archetype": "Unknown",
                "score_breakdown": {
                    "volume": 0.0,
                    "difficulty_balance": 0.0,
                    "acceptance": 0.0,
                    "recency": 0.0,
                    "contest": 0.0,
                },
                "formula": "N/A - user not found",
                "summary": "LeetCode user not found.",
            },
        }
