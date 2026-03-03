"""Demo mode API — pre-loaded candidate profiles for live demonstrations.

GET /api/demo/profiles          → list of available demo profiles
GET /api/demo/profiles/{name}   → full dashboard-ready response for a demo profile

No database needed — all data is hardcoded and deterministic.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

router = APIRouter(prefix="/api/demo", tags=["demo"])


# ── Pre-loaded demo profiles ─────────────────────────────

_DEMO_PROFILES: Dict[str, Dict[str, Any]] = {
    "strong-fullstack": {
        "name": "Alex Strong",
        "description": "Senior full-stack developer — high scores across all engines",
        "role_level": "senior",
        "pst_score": 87.4,
        "trust_level": "High Trust",
        "engines": {
            "github": {
                "normalized_score": 82.5,
                "raw_metrics": {
                    "total_repositories": 24,
                    "repos_analyzed": 10,
                    "total_commits": 847,
                    "commit_variance": 124.3,
                    "burst_flag": False,
                    "commit_message_entropy": 4.12,
                    "average_branches": 3.2,
                    "average_contributors": 2.1,
                    "average_repo_age_days": 892.0,
                    "language_count": 6,
                    "monthly_commits": [
                        {"date": "2024-01", "count": 45},
                        {"date": "2024-02", "count": 62},
                        {"date": "2024-03", "count": 58},
                        {"date": "2024-04", "count": 71},
                        {"date": "2024-05", "count": 53},
                        {"date": "2024-06", "count": 67},
                    ],
                },
            },
            "profile": {
                "normalized_score": 78.0,
                "raw_metrics": {
                    "skill_ratio": 0.85,
                    "project_ratio": 0.75,
                    "experience_ratio": 0.90,
                    "linkedin_profile_verified": True,
                    "collaboration_signal": True,
                },
            },
            "leetcode": {
                "normalized_score": 71.2,
                "raw_metrics": {
                    "total_solved": 187,
                    "easy_ratio": 0.35,
                    "medium_ratio": 0.50,
                    "hard_ratio": 0.15,
                    "acceptance_rate": 0.72,
                    "recent_in_90d": 23,
                },
            },
            "redflag": {
                "severity_score": 5.0,
                "raw_flags": {"flags": [], "total_flags": 0, "risk_level": "LOW RISK"},
            },
        },
        "narrative": {
            "archetype": "PROVEN_BUILDER",
            "headline": "Alex Strong — Verified Builder (PST 87/100)",
            "recommendation": "Strong candidate — proceed to cultural fit and system design rounds.",
        },
    },
    "academic-solver": {
        "name": "Jordan Academic",
        "description": "Mid-level candidate — strong LeetCode, limited GitHub activity",
        "role_level": "mid",
        "pst_score": 62.1,
        "trust_level": "Moderate Trust",
        "engines": {
            "github": {
                "normalized_score": 38.5,
                "raw_metrics": {
                    "total_repositories": 5,
                    "repos_analyzed": 5,
                    "total_commits": 67,
                    "commit_variance": 45.2,
                    "burst_flag": False,
                    "commit_message_entropy": 3.41,
                    "average_branches": 1.2,
                    "average_contributors": 1.0,
                    "average_repo_age_days": 210.0,
                    "language_count": 2,
                    "monthly_commits": [
                        {"date": "2024-03", "count": 12},
                        {"date": "2024-04", "count": 8},
                        {"date": "2024-05", "count": 22},
                        {"date": "2024-06", "count": 25},
                    ],
                },
            },
            "profile": {
                "normalized_score": 52.0,
                "raw_metrics": {
                    "skill_ratio": 0.60,
                    "project_ratio": 0.40,
                    "experience_ratio": 0.65,
                    "linkedin_profile_verified": True,
                    "collaboration_signal": False,
                },
            },
            "leetcode": {
                "normalized_score": 88.7,
                "raw_metrics": {
                    "total_solved": 342,
                    "easy_ratio": 0.25,
                    "medium_ratio": 0.55,
                    "hard_ratio": 0.20,
                    "acceptance_rate": 0.81,
                    "recent_in_90d": 45,
                },
            },
            "redflag": {
                "severity_score": 10.0,
                "raw_flags": {
                    "flags": [
                        {"flag": "No Collaboration Evidence", "severity": "LOW", "reason": "All repositories appear single-author"},
                    ],
                    "total_flags": 1,
                    "risk_level": "LOW RISK",
                },
            },
        },
        "narrative": {
            "archetype": "ACADEMIC_MIND",
            "headline": "Jordan Academic — Strong Problem-Solver, Limited Production Evidence (PST 62/100)",
            "recommendation": "Include a practical coding exercise to assess production engineering skills.",
        },
    },
    "red-flag-candidate": {
        "name": "Casey Flagged",
        "description": "Entry-level candidate — multiple red flags and inconsistencies",
        "role_level": "entry",
        "pst_score": 31.8,
        "trust_level": "Low Trust",
        "engines": {
            "github": {
                "normalized_score": 29.0,
                "raw_metrics": {
                    "total_repositories": 8,
                    "repos_analyzed": 8,
                    "total_commits": 312,
                    "commit_variance": 890.0,
                    "burst_flag": True,
                    "commit_message_entropy": 2.15,
                    "average_branches": 1.0,
                    "average_contributors": 1.0,
                    "average_repo_age_days": 45.0,
                    "language_count": 3,
                    "monthly_commits": [
                        {"date": "2024-05", "count": 8},
                        {"date": "2024-06", "count": 304},
                    ],
                },
            },
            "profile": {
                "normalized_score": 25.0,
                "raw_metrics": {
                    "skill_ratio": 0.30,
                    "project_ratio": 0.20,
                    "experience_ratio": 0.35,
                    "linkedin_profile_verified": False,
                    "collaboration_signal": False,
                },
            },
            "leetcode": {
                "normalized_score": 22.0,
                "raw_metrics": {
                    "total_solved": 15,
                    "easy_ratio": 0.87,
                    "medium_ratio": 0.13,
                    "hard_ratio": 0.0,
                    "acceptance_rate": 0.28,
                    "recent_in_90d": 15,
                },
            },
            "redflag": {
                "severity_score": 68.0,
                "raw_flags": {
                    "flags": [
                        {"flag": "Commit Burst Activity", "severity": "HIGH", "reason": "All commits concentrated in short time window"},
                        {"flag": "High Commit Variance", "severity": "MEDIUM", "reason": "Inconsistent commit distribution across repositories"},
                        {"flag": "Experience Timeline Mismatch", "severity": "HIGH", "reason": "Resume experience inconsistent with GitHub activity"},
                        {"flag": "Skill Evidence Weak", "severity": "MEDIUM", "reason": "Claimed skills lack GitHub validation"},
                        {"flag": "LinkedIn Not Verified", "severity": "LOW", "reason": "Public LinkedIn profile unreachable"},
                        {"flag": "No Collaboration Evidence", "severity": "LOW", "reason": "All repositories appear single-author"},
                    ],
                    "total_flags": 6,
                    "risk_level": "HIGH RISK",
                },
            },
        },
        "narrative": {
            "archetype": "INCONSISTENT",
            "headline": "Casey Flagged — Significant Inconsistencies Detected (PST 32/100)",
            "recommendation": "Proceed to technical interview with targeted questions on flagged discrepancies.",
        },
    },
}


# ── Endpoints ─────────────────────────────────────────────

@router.get("/profiles")
async def list_demo_profiles() -> List[Dict[str, Any]]:
    """List available demo profiles (name + description only)."""
    return [
        {
            "id": pid,
            "name": profile["name"],
            "description": profile["description"],
            "pst_score": profile["pst_score"],
            "trust_level": profile["trust_level"],
        }
        for pid, profile in _DEMO_PROFILES.items()
    ]


@router.get("/profiles/{profile_id}")
async def get_demo_profile(profile_id: str) -> Dict[str, Any]:
    """Return full dashboard-ready data for a demo profile."""
    profile = _DEMO_PROFILES.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Demo profile '{profile_id}' not found. "
            f"Available: {list(_DEMO_PROFILES.keys())}",
        )
    return profile
