"""Recruiter Trust Brief Generator.

Reads engine results from the database and synthesises a deterministic
intelligence report.  Supports ``run_id``-scoped queries (preferred) with
automatic fallback to *latest-per-user* for backwards compatibility.

Strength / concern rules (no dead zones):
  - GitHub >= 70       -> strength
  - GitHub 50-69       -> "average" (mentioned in context)
  - GitHub < 50        -> concern
  - Profile >= 70      -> strength
  - Profile 50-69      -> "average"
  - Profile < 50       -> concern
  - LeetCode >= 65     -> strength
  - LeetCode 30-64     -> "average"
  - LeetCode < 30      -> concern
  - RedFlag < 20       -> strength
  - RedFlag 20-39      -> "some flags"
  - RedFlag >= 40      -> concern
  - ProductMindset >= 60 -> strength
  - ProductMindset < 35 -> concern
  - DigitalFootprint >= 55 -> strength
  - DigitalFootprint < 25 -> concern

Strengths and concerns include actual scores for transparency.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models import (
    DigitalFootprintAnalysis,
    GitHubAnalysis,
    LeetCodeAnalysis,
    ProductMindsetAnalysis,
    ProfileConsistency,
    PSTReport,
    RedFlagAnalysis,
)


class RecruiterReportEngine:
    """Deterministic report builder."""

    async def generate(
        self,
        username: str,
        db: AsyncSession,
        *,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Generating recruiter report for {username} (run_id={run_id})")

        pst = await self._get(db, PSTReport, username, run_id)
        github = await self._get(db, GitHubAnalysis, username, run_id)
        profile = await self._get(db, ProfileConsistency, username, run_id)
        leetcode = await self._get(db, LeetCodeAnalysis, username, run_id)
        redflags = await self._get(db, RedFlagAnalysis, username, run_id)
        mindset = await self._get(db, ProductMindsetAnalysis, username, run_id)
        digital = await self._get(db, DigitalFootprintAnalysis, username, run_id)

        if not pst:
            return self._empty(username)

        strengths: List[str] = []
        concerns: List[str] = []

        # GitHub
        if github:
            gs = github.normalized_score
            if gs >= 70:
                strengths.append(f"Strong GitHub authenticity ({gs:.0f}/100) with consistent contributions.")
            elif gs >= 50:
                strengths.append(f"Average GitHub authenticity ({gs:.0f}/100) — moderate activity detected.")
            else:
                concerns.append(f"Weak GitHub signals ({gs:.0f}/100) — inconsistent or sparse activity.")

        # Profile
        if profile:
            ps = profile.normalized_score
            if ps >= 70:
                strengths.append(f"High resume consistency ({ps:.0f}/100) — skills and projects verified.")
            elif ps >= 50:
                strengths.append(f"Average resume consistency ({ps:.0f}/100) — partially verified.")
            else:
                concerns.append(f"Resume inconsistency ({ps:.0f}/100) — claims partially unverified.")

        # LeetCode
        if leetcode:
            ls = leetcode.normalized_score
            if ls >= 65:
                strengths.append(f"Solid problem-solving ({ls:.0f}/100) with balanced difficulty.")
            elif ls >= 30:
                strengths.append(f"Average problem-solving ({ls:.0f}/100) — some algorithmic practice.")
            else:
                concerns.append(f"Weak problem-solving ({ls:.0f}/100) — limited or no activity.")

        # Product Mindset
        if mindset:
            ms = mindset.normalized_score
            if ms >= 60:
                strengths.append(f"Builder mindset ({ms:.0f}/100) — original projects with documentation.")
            elif ms >= 35:
                strengths.append(f"Average project ownership ({ms:.0f}/100) — some original work.")
            else:
                concerns.append(f"Weak project ownership ({ms:.0f}/100) — mostly tutorials or forks.")

        # Digital Footprint
        if digital:
            ds = digital.normalized_score
            if ds >= 55:
                strengths.append(f"Visible digital presence ({ds:.0f}/100) — PRs, stars, or community activity.")
            elif ds >= 25:
                strengths.append(f"Average digital presence ({ds:.0f}/100) — some external activity.")
            else:
                concerns.append(f"Minimal digital footprint ({ds:.0f}/100) — limited external presence.")

        # Red flags
        if redflags:
            rs = redflags.severity_score
            if rs < 20:
                strengths.append(f"Low risk ({rs:.0f}/100 severity).")
            elif rs < 40:
                concerns.append(f"Some risk flags ({rs:.0f}/100 severity) — manual review advised.")
            else:
                concerns.append(f"Multiple red flags ({rs:.0f}/100 severity).")

        # Red-flag detail extraction (individual flags for transparency)
        flag_details: List[str] = []
        if redflags and hasattr(redflags, "raw_flags"):
            rf_data = redflags.raw_flags or {}
            for flag in rf_data.get("flags", [])[:5]:
                flag_details.append(f"[{flag.get('severity', '?')}] {flag.get('flag', 'Unknown')}")

        strengths = strengths[:5]
        concerns = concerns[:5]

        recommendation = self._recommend(pst.trust_level)

        return {
            "username": username,
            "pst_score": pst.pst_score,
            "trust_level": pst.trust_level,
            "strengths": strengths,
            "concerns": concerns,
            "flag_details": flag_details,
            "recommendation": recommendation,
            "engine_breakdown": pst.component_scores,
        }

    # ── helpers ───────────────────────────────────────────────

    @staticmethod
    async def _get(
        db: AsyncSession,
        model: Any,
        username: str,
        run_id: Optional[str],
    ) -> Optional[Any]:
        """Query by run_id first; fall back to latest row for the user."""
        if run_id and hasattr(model, "run_id"):
            result = await db.execute(
                select(model)
                .where(model.username == username, model.run_id == run_id)
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                return row
        # Fallback: latest
        result = await db.execute(
            select(model)
            .where(model.username == username)
            .order_by(model.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _recommend(trust_level: str) -> str:
        mapping = {
            "Highly Verified": "Proceed directly to final technical round.",
            "Strong": "Proceed to technical interview.",
            "Moderate": "Proceed with focused technical screening.",
            "Weak": "Manual review recommended before proceeding.",
        }
        return mapping.get(trust_level, "High risk profile. Strong review required.")

    @staticmethod
    def _empty(username: str) -> Dict[str, Any]:
        return {
            "username": username,
            "pst_score": 0.0,
            "trust_level": "No Data",
            "strengths": [],
            "concerns": [],
            "flag_details": [],
            "recommendation": "Run full analysis first.",
            "engine_breakdown": {},
        }
