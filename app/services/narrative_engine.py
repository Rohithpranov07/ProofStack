"""ENGINE 10 — Narrative Intelligence Engine.

Generates human-readable executive summaries from engine scores.
Pure function: deterministic input → deterministic output. No LLM.

Algorithm:
  1. Classify candidate into one of 6 archetypes based on score distribution
  2. Select template sentences per archetype
  3. Interpolate with actual metrics
  4. Produce a 3-paragraph executive summary

Archetypes:
  - PROVEN_BUILDER:  GitHub ≥ 75, Profile ≥ 70                → strong evidence of consistent development
  - ACADEMIC_MIND:   LeetCode ≥ 75, GitHub < 60               → strong problem-solving, limited production code
  - RISING_TALENT:   all ≥ 50, PST 50-70                      → promising but early-career
  - SPECIALIST:      one engine ≥ 80, others < 50              → deep in one area, gaps elsewhere
  - INCONSISTENT:    red_flag severity ≥ 40                    → significant discrepancies warrant review
  - INSUFFICIENT:    any engine failed or PST < 30             → not enough data for reliable assessment
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def generate_narrative(
    pst_score: float,
    github_score: float,
    profile_score: float,
    leetcode_score: float,
    redflag_severity: float,
    username: str,
    role_level: str = "mid",
    *,
    github_metrics: Optional[Dict[str, Any]] = None,
    leetcode_metrics: Optional[Dict[str, Any]] = None,
    engine_failures: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Generate a deterministic executive narrative from engine scores.

    Returns:
        {
            "archetype": str,
            "headline": str,
            "summary": str,        # 3-paragraph narrative
            "strengths": [str],
            "concerns": [str],
            "recommendation": str,
        }
    """
    failures = engine_failures or []
    gh = github_metrics or {}
    lc = leetcode_metrics or {}

    archetype = _classify(
        pst_score, github_score, profile_score, leetcode_score,
        redflag_severity, failures,
    )

    strengths = _identify_strengths(github_score, profile_score, leetcode_score, gh, lc)
    concerns = _identify_concerns(github_score, profile_score, leetcode_score, redflag_severity, gh)
    headline = _headline(archetype, username, pst_score)
    summary = _build_summary(
        archetype, username, role_level, pst_score,
        github_score, profile_score, leetcode_score,
        redflag_severity, gh, lc,
    )
    recommendation = _recommend(archetype, role_level, pst_score)

    return {
        "archetype": archetype,
        "headline": headline,
        "summary": summary,
        "strengths": strengths,
        "concerns": concerns,
        "recommendation": recommendation,
    }


# ── Classification ────────────────────────────────────────

def _classify(
    pst: float, gh: float, prof: float, lc: float,
    rf: float, failures: list[str],
) -> str:
    if failures or pst < 30:
        return "INSUFFICIENT"
    if rf >= 40:
        return "INCONSISTENT"
    if gh >= 75 and prof >= 70:
        return "PROVEN_BUILDER"
    if lc >= 75 and gh < 60:
        return "ACADEMIC_MIND"
    if max(gh, prof, lc) >= 80 and min(gh, prof, lc) < 50:
        return "SPECIALIST"
    return "RISING_TALENT"


# ── Headline ──────────────────────────────────────────────

def _headline(archetype: str, username: str, pst: float) -> str:
    templates = {
        "PROVEN_BUILDER": f"{username} — Verified Builder (PST {pst:.0f}/100)",
        "ACADEMIC_MIND": f"{username} — Strong Problem-Solver, Limited Production Evidence (PST {pst:.0f}/100)",
        "RISING_TALENT": f"{username} — Promising Early-Stage Developer (PST {pst:.0f}/100)",
        "SPECIALIST": f"{username} — Domain Specialist with Skill Gaps (PST {pst:.0f}/100)",
        "INCONSISTENT": f"{username} — Significant Inconsistencies Detected (PST {pst:.0f}/100)",
        "INSUFFICIENT": f"{username} — Insufficient Data for Assessment (PST {pst:.0f}/100)",
    }
    return templates.get(archetype, f"{username} — PST {pst:.0f}/100")


# ── Strengths & Concerns ─────────────────────────────────

def _identify_strengths(
    gh: float, prof: float, lc: float,
    gh_metrics: Dict[str, Any], lc_metrics: Dict[str, Any],
) -> list[str]:
    strengths = []
    if gh >= 70:
        commits = gh_metrics.get("total_commits", 0)
        strengths.append(f"Strong GitHub presence ({commits} commits across analyzed repos)")
    if prof >= 70:
        strengths.append("Resume claims well-corroborated by public code and profiles")
    if lc >= 70:
        total = lc_metrics.get("total_solved", 0)
        strengths.append(f"Solid problem-solving evidence ({total} LeetCode problems solved)")
    if gh_metrics.get("commit_message_entropy", 0) > 3.5:
        strengths.append("High commit message quality (Shannon entropy > 3.5 bits)")
    if gh_metrics.get("average_contributors", 0) > 1.5:
        strengths.append("Evidence of collaborative development across repositories")
    if not strengths:
        strengths.append("No standout strengths identified from available data")
    return strengths


def _identify_concerns(
    gh: float, prof: float, lc: float,
    rf: float, gh_metrics: Dict[str, Any],
) -> list[str]:
    concerns = []
    if gh < 50:
        concerns.append("Limited GitHub activity — may indicate private repos or alternative platforms")
    if prof < 50:
        concerns.append("Low resume-to-code correlation — claimed skills lack public evidence")
    if lc < 40:
        concerns.append("Minimal algorithmic problem-solving evidence")
    if rf >= 30:
        concerns.append(f"Red flag severity score of {rf:.0f}/100 — manual review recommended")
    if gh_metrics.get("burst_flag"):
        concerns.append("Commit burst detected — majority of commits in a narrow time window")
    if not concerns:
        concerns.append("No significant concerns identified")
    return concerns


# ── Summary builder ───────────────────────────────────────

def _build_summary(
    archetype: str, username: str, role: str, pst: float,
    gh: float, prof: float, lc: float, rf: float,
    gh_metrics: Dict[str, Any], lc_metrics: Dict[str, Any],
) -> str:
    role_label = {"entry": "entry-level", "mid": "mid-level", "senior": "senior"}.get(role, role)

    # Paragraph 1: Overview
    p1_templates = {
        "PROVEN_BUILDER": (
            f"{username} demonstrates consistent, verifiable engineering output. "
            f"With a ProofStack Trust Score of {pst:.1f}/100 for {role_label} evaluation, "
            f"this candidate shows strong alignment between claimed experience and public evidence."
        ),
        "ACADEMIC_MIND": (
            f"{username} shows strong algorithmic capability with "
            f"{lc_metrics.get('total_solved', 0)} LeetCode problems solved, "
            f"but limited production-grade GitHub activity (score: {gh:.0f}/100). "
            f"PST: {pst:.1f}/100 for {role_label}."
        ),
        "RISING_TALENT": (
            f"{username} presents as a developing engineer with balanced but modest scores "
            f"across all dimensions. PST: {pst:.1f}/100 for {role_label} evaluation. "
            f"The profile suggests growth trajectory rather than established expertise."
        ),
        "SPECIALIST": (
            f"{username} shows deep capability in one area but significant gaps in others. "
            f"PST: {pst:.1f}/100 for {role_label}. This pattern is common for contributors "
            f"focused on a specific domain or technology stack."
        ),
        "INCONSISTENT": (
            f"{username} has a red flag severity of {rf:.0f}/100, indicating "
            f"material discrepancies between claimed and observed activity. "
            f"PST: {pst:.1f}/100 for {role_label}. Manual verification is strongly recommended."
        ),
        "INSUFFICIENT": (
            f"Insufficient public data available to produce a reliable assessment for {username}. "
            f"PST: {pst:.1f}/100. One or more analysis engines failed or returned no data."
        ),
    }
    p1 = p1_templates.get(archetype, f"PST: {pst:.1f}/100 for {username}.")

    # Paragraph 2: Score breakdown
    p2 = (
        f"Score breakdown: GitHub Authenticity {gh:.0f}/100, "
        f"Profile Consistency {prof:.0f}/100, "
        f"LeetCode Pattern {lc:.0f}/100. "
        f"Red flag severity: {rf:.0f}/100 "
        f"({'elevated' if rf >= 30 else 'within normal range'})."
    )

    # Paragraph 3: Context
    commits = gh_metrics.get("total_commits", 0)
    repos = gh_metrics.get("total_repositories", 0)
    langs = gh_metrics.get("language_count", 0)
    p3 = (
        f"Analysis based on {repos} public repositories, {commits} commits, "
        f"and {langs} programming language{'s' if langs != 1 else ''} detected. "
        f"All scores are deterministic and reproducible — "
        f"identical inputs will always produce identical outputs."
    )

    return f"{p1}\n\n{p2}\n\n{p3}"


# ── Recommendation ────────────────────────────────────────

def _recommend(archetype: str, role: str, pst: float) -> str:
    if archetype == "INSUFFICIENT":
        return "Request additional portfolio links or conduct live technical assessment."
    if archetype == "INCONSISTENT":
        return "Proceed to technical interview with targeted questions on flagged discrepancies."
    if archetype == "PROVEN_BUILDER" and pst >= 80:
        return "Strong candidate — proceed to cultural fit and system design rounds."
    if archetype == "ACADEMIC_MIND":
        return "Include a practical coding exercise to assess production engineering skills."
    if archetype == "SPECIALIST":
        return "Evaluate breadth requirements for the role — specialist may excel in focused positions."
    # RISING_TALENT or other
    if role == "entry":
        return "Suitable for entry-level — potential for growth with mentorship."
    return "Consider for the role with follow-up on areas of lower evidence."
