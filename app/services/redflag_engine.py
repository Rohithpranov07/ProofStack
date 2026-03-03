"""ENGINE 4 — Global Red Flag Detection Engine.

Cross-engine risk & integrity analyzer.
Consumes raw metrics from Engines 1–3 plus advanced anomaly data
and detects systemic inconsistencies.

Deterministic severity scoring (0–100):
──────────────────────────────────────────────────────────────
  Flag                          | Severity | Points
  ──────────────────────────────|──────────|───────
  Commit Burst Activity         | HIGH     |  20
  High Commit Variance          | MEDIUM   |  10
  Experience Timeline Mismatch  | HIGH     |  15
  Skill Evidence Weak           | MEDIUM   |  10
  Project Not Found             | HIGH     |  15
  LinkedIn Not Verified         | LOW      |   5
  LeetCode No Activity          | LOW      |   5
  Easy-Dominant Problem Solving | MEDIUM   |   8
  Low Acceptance Rate           | MEDIUM   |   7
  No Collaboration Evidence     | LOW      |   5
  Data Unavailable (per engine) | LOW      |   3
  LOC Anomaly Detected          | MEDIUM   |   8
  Repetitive Commit Messages    | MEDIUM   |   7
  Cross-Repo Commit Overlap     | MEDIUM   |   8
  ──────────────────────────────|──────────|───────
  Max (clamped)                              100

Risk levels:
  severity >= 60 → HIGH RISK
  severity >= 30 → MODERATE RISK
  severity <  30 → LOW RISK

Missing data:
  When engine metrics are empty, this is treated as UNKNOWN —
  a small penalty is applied (not assumed perfect).

Every number is reproducible — same inputs always yield the same outputs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import logger


class RedFlagEngine:
    """Pure-function engine: cross-engine metrics → deterministic flags + severity."""

    async def analyze(
        self,
        username: str,
        github: Dict[str, Any],
        profile: Dict[str, Any],
        leetcode: Dict[str, Any],
        *,
        advanced: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run red-flag detection across all engine metrics.

        Args:
            username: Candidate identifier.
            github: Raw metrics from Engine 1 (GitHub Authenticity).
            profile: Raw metrics from Engine 2 (Profile Consistency).
            leetcode: Raw metrics from Engine 3 (LeetCode Pattern).
            advanced: Raw metrics from Engine 1b (Advanced GitHub).

        Returns:
            {
                "username": str,
                "raw_flags": { "flags": [...], "total_flags": int, "risk_level": str },
                "severity_score": float,
                "explanation": { ... },
            }
        """

        logger.info(f"Starting red flag analysis for {username}")

        flags: List[Dict[str, str]] = []
        severity_score: float = 0.0

        github_available = bool(github)
        profile_available = bool(profile)
        leetcode_available = bool(leetcode)

        # ── 0. Data availability penalties ────────────────────────
        if not github_available:
            flags.append({
                "flag": "GitHub Data Unavailable",
                "severity": "LOW",
                "reason": "GitHub engine produced no data — cannot verify code activity",
            })
            severity_score += 3

        if not profile_available:
            flags.append({
                "flag": "Profile Data Unavailable",
                "severity": "LOW",
                "reason": "Profile consistency engine produced no data — cannot verify claims",
            })
            severity_score += 3

        if not leetcode_available:
            flags.append({
                "flag": "LeetCode Data Unavailable",
                "severity": "LOW",
                "reason": "LeetCode engine produced no data — cannot assess problem-solving",
            })
            severity_score += 3

        # ── 1. Commit Burst Activity ─────────────────────────────
        if github.get("burst_flag"):
            flags.append({
                "flag": "Commit Burst Activity",
                "severity": "HIGH",
                "reason": "All commits concentrated in short time window",
            })
            severity_score += 20

        # ── 2. High Commit Variance ──────────────────────────────
        if github.get("commit_variance", 0) > 500:
            flags.append({
                "flag": "High Commit Variance",
                "severity": "MEDIUM",
                "reason": "Inconsistent commit distribution across repositories",
            })
            severity_score += 10

        # ── 3. Experience Timeline Mismatch ──────────────────────
        exp_ratio = profile.get("experience_ratio", -1)
        if exp_ratio == -1 and profile_available:
            severity_score += 2
        elif exp_ratio != -1 and exp_ratio < 0.5:
            flags.append({
                "flag": "Experience Timeline Mismatch",
                "severity": "HIGH",
                "reason": "Resume experience inconsistent with GitHub activity",
            })
            severity_score += 15

        # ── 4. Skill Evidence Weak ───────────────────────────────
        skill_ratio = profile.get("skill_ratio", -1)
        if skill_ratio == -1 and profile_available:
            severity_score += 2
        elif skill_ratio != -1 and skill_ratio < 0.6:
            flags.append({
                "flag": "Skill Evidence Weak",
                "severity": "MEDIUM",
                "reason": "Claimed skills lack GitHub validation",
            })
            severity_score += 10

        # ── 5. Project Not Found ─────────────────────────────────
        project_ratio = profile.get("project_ratio", -1)
        if project_ratio == -1 and profile_available:
            severity_score += 2
        elif project_ratio != -1 and project_ratio < 0.5:
            flags.append({
                "flag": "Project Not Found",
                "severity": "HIGH",
                "reason": "Resume projects missing from GitHub",
            })
            severity_score += 15

        # ── 6. LinkedIn Not Verified ─────────────────────────────
        if profile_available and not profile.get("linkedin_profile_verified", False):
            flags.append({
                "flag": "LinkedIn Not Verified",
                "severity": "LOW",
                "reason": "Public LinkedIn profile unreachable",
            })
            severity_score += 5

        # ── 7. LeetCode No Activity ──────────────────────────────
        if leetcode_available and leetcode.get("total_solved", 0) == 0:
            flags.append({
                "flag": "LeetCode No Activity",
                "severity": "LOW",
                "reason": "LeetCode profile exists but no problems solved",
            })
            severity_score += 5

        # ── 8. Easy-Dominant Problem Solving ──────────────────────
        if (
            leetcode.get("easy_ratio", 0) > 0.8
            and leetcode.get("total_solved", 0) > 50
        ):
            flags.append({
                "flag": "Easy-Dominant Problem Solving",
                "severity": "MEDIUM",
                "reason": "High easy-problem concentration",
            })
            severity_score += 8

        # ── 9. Low Acceptance Rate ────────────────────────────────
        acc = leetcode.get("acceptance_rate", -1)
        if acc != -1 and acc < 0.3:
            flags.append({
                "flag": "Low Acceptance Rate",
                "severity": "MEDIUM",
                "reason": "High failed attempt ratio",
            })
            severity_score += 7

        # ── 10. No Collaboration Evidence ─────────────────────────
        avg_contribs = github.get("average_contributors", -1)
        if avg_contribs != -1 and avg_contribs <= 1:
            flags.append({
                "flag": "No Collaboration Evidence",
                "severity": "LOW",
                "reason": "All repositories appear single-author",
            })
            severity_score += 5

        # ── 11–13. Advanced anomaly flags ─────────────────────────
        if advanced:
            if advanced.get("loc_anomaly_ratio", 0) > 0.15:
                flags.append({
                    "flag": "LOC Anomaly Detected",
                    "severity": "MEDIUM",
                    "reason": "Extreme code-change spikes in commit history",
                })
                severity_score += 8

            if advanced.get("repetitive_message_ratio", 0) > 0.4:
                flags.append({
                    "flag": "Repetitive Commit Messages",
                    "severity": "MEDIUM",
                    "reason": "High ratio of duplicate commit messages",
                })
                severity_score += 7

            if advanced.get("repo_overlap_score", 0) > 3:
                flags.append({
                    "flag": "Cross-Repo Commit Overlap",
                    "severity": "MEDIUM",
                    "reason": "Simultaneous commits across multiple repos",
                })
                severity_score += 8

        # ── Severity normalization ────────────────────────────────
        severity_score = round(min(severity_score, 100.0), 2)

        # ── Risk level classification ─────────────────────────────
        if severity_score >= 60:
            risk_level = "HIGH RISK"
        elif severity_score >= 30:
            risk_level = "MODERATE RISK"
        else:
            risk_level = "LOW RISK"

        raw_flags: Dict[str, Any] = {
            "flags": flags,
            "total_flags": len(flags),
            "risk_level": risk_level,
        }

        explanation: Dict[str, Any] = {
            "severity_score": severity_score,
            "risk_level": risk_level,
            "data_availability": {
                "github": github_available,
                "profile": profile_available,
                "leetcode": leetcode_available,
                "advanced": advanced is not None and bool(advanced),
            },
            "interpretation": self._interpret(risk_level),
        }

        return {
            "username": username,
            "raw_flags": raw_flags,
            "severity_score": severity_score,
            "explanation": explanation,
        }

    # ── interpretation helper ─────────────────────────────────────

    @staticmethod
    def _interpret(level: str) -> str:
        """Return a human-readable interpretation for the risk level."""
        if level == "HIGH RISK":
            return "Multiple systemic inconsistencies detected."
        elif level == "MODERATE RISK":
            return "Some inconsistencies present. Manual review recommended."
        return "No major systemic red flags detected."
