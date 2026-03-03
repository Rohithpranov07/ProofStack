"""Profile Consistency Engine — Engine 2 of ProofStack.

Cross-verifies resume claims, GitHub activity, and LinkedIn data
to produce a deterministic consistency score.

=== WHAT IS VERIFIED ===

1. Skill Consistency (Resume ↔ GitHub)
   - Each resume skill is matched against GitHub repository languages.
   - Claimed years are compared to the earliest repo using that language.
   - A 0.5-year tolerance is applied (grace period).

2. Project Consistency (Resume ↔ GitHub)
   - Each resume project name is checked against GitHub repo names.
   - Case-insensitive exact match.

3. Experience Timeline Consistency
   - Each resume experience start_date is compared to the earliest
     GitHub repo created_at.
   - If a claimed job started *on or after* the earliest GitHub activity,
     it is verifiable. If it started *before*, it cannot be verified.

4. LinkedIn Verification
   - Profile URL reachability (HTTP 200 check, no auth).
   - Skills cross-check: LinkedIn skills not on resume are flagged.
   - Experience cross-check: LinkedIn companies not on resume are flagged.

5. Collaboration Signal
   - Repos with >1 contributor indicate real team collaboration.

=== SCORING FORMULA (explicit, no hidden weights) ===

  score  = 0
  score += skill_ratio     × 30       (up to 30 pts)
  score += project_ratio   × 20       (up to 20 pts)
  score += experience_ratio × 20      (up to 20 pts)
  score += 15 if linkedin_verified    (flat 15 pts)
  score += 15 if collaboration_signal (flat 15 pts)

  normalized_score = clamp(score, 0, 100)

Every component is surfaced in the explanation dict.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.schemas.profile import LinkedInStructured, ResumeStructured
from app.services.github_client import GitHubClient
from app.services.linkedin_client import LinkedInClient

_MAX_CONTRIBUTOR_REPOS = 20  # limit contributor fetches

# Framework/tool → parent language mapping for broader skill verification
# e.g. "React" should match repos with language "JavaScript" or "TypeScript"
_SKILL_TO_LANGUAGES: Dict[str, List[str]] = {
    "react": ["javascript", "typescript"],
    "react.js": ["javascript", "typescript"],
    "reactjs": ["javascript", "typescript"],
    "next.js": ["javascript", "typescript"],
    "nextjs": ["javascript", "typescript"],
    "angular": ["javascript", "typescript"],
    "vue": ["javascript", "typescript"],
    "vue.js": ["javascript", "typescript"],
    "svelte": ["javascript", "typescript"],
    "nuxt": ["javascript", "typescript"],
    "node.js": ["javascript", "typescript"],
    "nodejs": ["javascript", "typescript"],
    "express": ["javascript", "typescript"],
    "express.js": ["javascript", "typescript"],
    "nestjs": ["javascript", "typescript"],
    "jquery": ["javascript"],
    "webpack": ["javascript", "typescript"],
    "vite": ["javascript", "typescript"],
    "tailwind": ["javascript", "typescript", "css"],
    "tailwindcss": ["javascript", "typescript", "css"],
    "bootstrap": ["javascript", "css"],
    "django": ["python"],
    "flask": ["python"],
    "fastapi": ["python"],
    "pandas": ["python", "jupyter notebook"],
    "numpy": ["python", "jupyter notebook"],
    "pytorch": ["python", "jupyter notebook"],
    "tensorflow": ["python", "jupyter notebook"],
    "keras": ["python", "jupyter notebook"],
    "scikit-learn": ["python", "jupyter notebook"],
    "celery": ["python"],
    "spring": ["java", "kotlin"],
    "spring boot": ["java", "kotlin"],
    "rails": ["ruby"],
    "ruby on rails": ["ruby"],
    "laravel": ["php"],
    "symfony": ["php"],
    "flutter": ["dart"],
    "swiftui": ["swift"],
    "react native": ["javascript", "typescript"],
    ".net": ["c#"],
    "asp.net": ["c#"],
    "entity framework": ["c#"],
    "gin": ["go"],
    "echo": ["go"],
    "fiber": ["go"],
    "actix": ["rust"],
    "rocket": ["rust"],
    "docker": ["dockerfile"],
    "kubernetes": ["yaml", "go"],
    "terraform": ["hcl"],
    "ansible": ["yaml", "python"],
}


class ProfileConsistencyEngine:
    """Deterministic resume ↔ GitHub ↔ LinkedIn cross-verification."""

    def __init__(self) -> None:
        self.github = GitHubClient()
        self.linkedin = LinkedInClient()

    # ── public entry point ──────────────────────────────────

    async def analyze(
        self,
        username: str,
        resume_data: ResumeStructured,
        linkedin_data: Optional[LinkedInStructured] = None,
        *,
        repos: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run full cross-verification and return structured result dict.

        Args:
            repos: Pre-fetched GitHub repos. If None, fetches internally.

        Returns:
            {
                "username": str,
                "raw_metrics": { ... },
                "normalized_score": float,
                "explanation": { ... }
            }
        """
        logger.info(f"Starting profile consistency analysis for {username}")
        if repos is None:
            repos = await self.github.get_repos(username)

        if not repos:
            return self._empty(username)

        logger.info(f"Profile cross-verification in progress for {username}")
        now = datetime.now(timezone.utc)

        # ── GitHub data collection (concurrent) ──────────────

        language_first_seen: Dict[str, datetime] = {}
        repo_names: List[str] = []
        contributor_map: Dict[str, int] = {}

        for repo in repos:
            repo_names.append(repo["name"].lower())

            language: str | None = repo.get("language")
            created_str: str = repo["created_at"]
            created_at = datetime.fromisoformat(
                created_str.replace("Z", "+00:00")
            )

            if language:
                lang_lower = language.lower()
                if lang_lower not in language_first_seen:
                    language_first_seen[lang_lower] = created_at
                else:
                    language_first_seen[lang_lower] = min(
                        language_first_seen[lang_lower], created_at
                    )

        # Fetch contributors concurrently (limited to avoid API abuse)
        limited_repos = repos[:_MAX_CONTRIBUTOR_REPOS]

        async def _fetch_contributors(repo: Dict[str, Any]) -> tuple[str, int]:
            try:
                contributors = await self.github.get_contributors(
                    username, repo["name"]
                )
                return (repo["name"].lower(), len(contributors))
            except Exception:
                return (repo["name"].lower(), 1)

        contributor_results = await asyncio.gather(
            *[_fetch_contributors(r) for r in limited_repos]
        )
        for name, count in contributor_results:
            contributor_map[name] = count

        # ── 1. Skill consistency (Resume ↔ GitHub) ─────────
        # We check: (a) repo primary language, (b) framework→language mapping,
        # (c) repo names, descriptions, and topics for keyword presence.

        skill_mismatches: List[Dict[str, Any]] = []
        skill_verified = 0

        # Build a set of all repo text for keyword-based matching
        repo_text_tokens: set[str] = set()
        repo_topic_tokens: set[str] = set()
        for repo in repos:
            repo_text_tokens.add(repo["name"].lower())
            desc = (repo.get("description") or "").lower()
            for word in desc.split():
                repo_text_tokens.add(word.strip(".,;:!?()[]{}"))
            for topic in (repo.get("topics") or []):
                repo_topic_tokens.add(topic.lower())
                repo_text_tokens.add(topic.lower())

        for skill in resume_data.skills:
            matched = False
            skill_lower = skill.name.lower()

            # (a) Direct language match
            for lang, first_seen in language_first_seen.items():
                if skill_lower in lang or lang in skill_lower:
                    matched = True
                    actual_years = (now - first_seen).total_seconds() / (
                        365.25 * 86_400
                    )
                    if actual_years + 0.5 >= skill.years:
                        skill_verified += 1
                    else:
                        skill_mismatches.append(
                            {
                                "skill": skill.name,
                                "claimed_years": skill.years,
                                "observed_years": round(actual_years, 2),
                                "issue": (
                                    f"Claimed {skill.years}y but GitHub shows "
                                    f"{actual_years:.2f}y (tolerance 0.5y)"
                                ),
                            }
                        )
                    break

            # (b) Framework → parent language mapping
            if not matched and skill_lower in _SKILL_TO_LANGUAGES:
                parent_langs = _SKILL_TO_LANGUAGES[skill_lower]
                for pl in parent_langs:
                    if pl in language_first_seen:
                        matched = True
                        first_seen = language_first_seen[pl]
                        actual_years = (now - first_seen).total_seconds() / (
                            365.25 * 86_400
                        )
                        if actual_years + 0.5 >= skill.years:
                            skill_verified += 1
                        else:
                            skill_mismatches.append(
                                {
                                    "skill": skill.name,
                                    "claimed_years": skill.years,
                                    "observed_years": round(actual_years, 2),
                                    "issue": (
                                        f"Claimed {skill.years}y but parent language "
                                        f"'{pl}' shows {actual_years:.2f}y"
                                    ),
                                }
                            )
                        break

            # (c) Keyword presence in repo names, descriptions, or topics
            if not matched:
                # Check if the skill name appears in any repo name, description, or topic
                skill_words = skill_lower.replace(".", "").replace("-", "").replace(" ", "")
                for token in repo_text_tokens | repo_topic_tokens:
                    clean_token = token.replace(".", "").replace("-", "")
                    if skill_words in clean_token or clean_token in skill_words:
                        matched = True
                        skill_verified += 1
                        break
                # Also check direct substring in topics
                if not matched:
                    for topic in repo_topic_tokens:
                        if skill_lower in topic or topic in skill_lower:
                            matched = True
                            skill_verified += 1
                            break

            if not matched:
                skill_mismatches.append(
                    {
                        "skill": skill.name,
                        "issue": "No matching GitHub language found",
                    }
                )

        total_skills = max(len(resume_data.skills), 1)
        skill_ratio = round(skill_verified / total_skills, 4)

        # ── 2. Project consistency ──────────────────────────
        # Multi-signal matching: name, github_url, description, topics

        project_verified = 0
        project_mismatches: List[Dict[str, str]] = []

        # Build a richer lookup from repos: name, description, topics
        repo_lookup: List[Dict[str, str]] = []
        for repo in repos:
            rn = repo["name"].lower().strip()
            rn_norm = rn.replace("-", "").replace("_", "").replace(" ", "")
            desc = (repo.get("description") or "").lower().strip()
            desc_norm = desc.replace("-", "").replace("_", "").replace(" ", "")
            topics = [t.lower() for t in (repo.get("topics") or [])]
            html_url = (repo.get("html_url") or "").lower()
            repo_lookup.append({
                "name": rn,
                "name_norm": rn_norm,
                "desc": desc,
                "desc_norm": desc_norm,
                "topics_str": " ".join(topics),
                "html_url": html_url,
            })

        for project in resume_data.projects:
            proj_lower = project.name.lower().strip()
            proj_normalised = proj_lower.replace("-", "").replace("_", "").replace(" ", "")
            found = False

            # Signal 1: If the user provided a github_url, match directly
            if hasattr(project, "github_url") and project.github_url:
                proj_url = project.github_url.lower().strip().rstrip("/")
                for rl in repo_lookup:
                    if rl["html_url"] and proj_url.endswith(rl["name"]):
                        found = True
                        break
                    if rl["html_url"] and rl["html_url"].rstrip("/") == proj_url:
                        found = True
                        break

            # Signal 2: Name matching (exact, normalised, substring)
            if not found:
                for rl in repo_lookup:
                    # Exact match
                    if proj_lower == rl["name"]:
                        found = True
                        break
                    # Normalised match (e.g. "my-app" vs "myapp")
                    if proj_normalised == rl["name_norm"]:
                        found = True
                        break
                    # Substring match (e.g. "Portfolio Website" contains "portfolio")
                    if len(proj_normalised) >= 3 and (
                        proj_normalised in rl["name_norm"]
                        or rl["name_norm"] in proj_normalised
                    ):
                        found = True
                        break

            # Signal 3: Match project name against repo descriptions
            if not found and len(proj_normalised) >= 4:
                for rl in repo_lookup:
                    if rl["desc_norm"] and proj_normalised in rl["desc_norm"]:
                        found = True
                        break
                    # Also check if any significant word from the project name
                    # appears in the repo description
                    proj_words = [w for w in proj_lower.split() if len(w) >= 4]
                    if proj_words and rl["desc"]:
                        matches = sum(1 for w in proj_words if w in rl["desc"])
                        if matches >= max(len(proj_words) * 0.5, 1):
                            found = True
                            break

            # Signal 4: Match against repo topics
            if not found:
                for rl in repo_lookup:
                    if rl["topics_str"] and proj_normalised in rl["topics_str"]:
                        found = True
                        break

            if found:
                project_verified += 1
            else:
                project_mismatches.append(
                    {
                        "project": project.name,
                        "issue": "Project not found in GitHub repositories",
                    }
                )

        total_projects = max(len(resume_data.projects), 1)
        project_ratio = round(project_verified / total_projects, 4)

        # ── 3. Experience timeline ──────────────────────────

        earliest_repo_date = min(
            datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            for r in repos
        ).date()

        experience_verified = 0
        experience_mismatches: List[Dict[str, str]] = []

        for exp in resume_data.experience:
            if not exp.start_date:
                # No start date available — count as verified (benefit of the doubt)
                experience_verified += 1
                continue
            if exp.start_date >= earliest_repo_date:
                experience_verified += 1
            else:
                experience_mismatches.append(
                    {
                        "company": exp.company,
                        "claimed_start": str(exp.start_date),
                        "earliest_github": str(earliest_repo_date),
                        "issue": (
                            "Experience start date predates earliest "
                            "GitHub activity — cannot be verified"
                        ),
                    }
                )

        total_experience = max(len(resume_data.experience), 1)
        experience_ratio = round(experience_verified / total_experience, 4)

        # ── 4. LinkedIn verification ────────────────────────

        linkedin_verified = False
        linkedin_skill_mismatch: List[str] = []
        linkedin_experience_mismatch: List[str] = []

        if linkedin_data:
            # Profile URL reachability
            if linkedin_data.profile_url:
                linkedin_verified = await self.linkedin.verify_profile(
                    str(linkedin_data.profile_url)
                )

            # Skills cross-check (LinkedIn skills not on resume)
            if linkedin_data.skills:
                resume_skill_names = {
                    s.name.lower() for s in resume_data.skills
                }
                for ls in linkedin_data.skills:
                    if ls.lower() not in resume_skill_names:
                        linkedin_skill_mismatch.append(ls)

            # Experience cross-check (LinkedIn companies not on resume)
            if linkedin_data.experience:
                resume_companies = {
                    e.company.lower() for e in resume_data.experience
                }
                for le in linkedin_data.experience:
                    if le.company.lower() not in resume_companies:
                        linkedin_experience_mismatch.append(le.company)

        # ── 5. Collaboration signal ─────────────────────────

        multi_contributor_repos = sum(
            1 for c in contributor_map.values() if c > 1
        )
        collaboration_signal = multi_contributor_repos > 0

        # ── Assemble output ─────────────────────────────────

        raw_metrics: Dict[str, Any] = {
            "skill_ratio": skill_ratio,
            "skill_verified": skill_verified,
            "skill_total": len(resume_data.skills),
            "skill_mismatches": skill_mismatches,
            "project_ratio": project_ratio,
            "project_verified": project_verified,
            "project_total": len(resume_data.projects),
            "project_mismatches": project_mismatches,
            "experience_ratio": experience_ratio,
            "experience_verified": experience_verified,
            "experience_total": len(resume_data.experience),
            "experience_mismatches": experience_mismatches,
            "earliest_github_repo_date": str(earliest_repo_date),
            "linkedin_profile_verified": linkedin_verified,
            "linkedin_skill_mismatch": linkedin_skill_mismatch,
            "linkedin_experience_mismatch": linkedin_experience_mismatch,
            "multi_contributor_repos": multi_contributor_repos,
        }

        normalized_score = self._calculate_score(
            skill_ratio,
            project_ratio,
            experience_ratio,
            linkedin_verified,
            collaboration_signal,
        )

        explanation = self._build_explanation(
            skill_ratio,
            project_ratio,
            experience_ratio,
            linkedin_verified,
            collaboration_signal,
            normalized_score,
        )

        return {
            "username": username,
            "raw_metrics": raw_metrics,
            "normalized_score": normalized_score,
            "explanation": explanation,
        }

    # ── deterministic scoring ───────────────────────────────

    @staticmethod
    def _calculate_score(
        skill_ratio: float,
        project_ratio: float,
        experience_ratio: float,
        linkedin_verified: bool,
        collaboration_signal: bool,
    ) -> float:
        """Apply the explicit scoring formula documented in the module docstring.

        score  = skill_ratio × 30
               + project_ratio × 20
               + experience_ratio × 20
               + 15 if linkedin_verified
               + 15 if collaboration_signal
        clamped to [0, 100].
        """
        score = 0.0
        score += skill_ratio * 30.0
        score += project_ratio * 20.0
        score += experience_ratio * 20.0

        if linkedin_verified:
            score += 15.0

        if collaboration_signal:
            score += 15.0

        return round(max(0.0, min(score, 100.0)), 2)

    # ── explanation builder ─────────────────────────────────

    @staticmethod
    def _build_explanation(
        skill_ratio: float,
        project_ratio: float,
        experience_ratio: float,
        linkedin_verified: bool,
        collaboration_signal: bool,
        final_score: float,
    ) -> Dict[str, Any]:
        """Produce a fully deterministic explanation dict."""
        skill_pts = round(skill_ratio * 30.0, 2)
        project_pts = round(project_ratio * 20.0, 2)
        experience_pts = round(experience_ratio * 20.0, 2)
        linkedin_pts = 15.0 if linkedin_verified else 0.0
        collab_pts = 15.0 if collaboration_signal else 0.0

        return {
            "formula": (
                "score = skill_ratio×30 + project_ratio×20 "
                "+ experience_ratio×20 + linkedin_bonus(15) "
                "+ collaboration_bonus(15)"
            ),
            "components": {
                "skill_pts": {
                    "value": skill_pts,
                    "formula": "skill_ratio × 30",
                    "input": skill_ratio,
                },
                "project_pts": {
                    "value": project_pts,
                    "formula": "project_ratio × 20",
                    "input": project_ratio,
                },
                "experience_pts": {
                    "value": experience_pts,
                    "formula": "experience_ratio × 20",
                    "input": experience_ratio,
                },
                "linkedin_pts": {
                    "value": linkedin_pts,
                    "formula": "15 if linkedin_verified else 0",
                    "input": linkedin_verified,
                },
                "collaboration_pts": {
                    "value": collab_pts,
                    "formula": "15 if collaboration_signal else 0",
                    "input": collaboration_signal,
                },
            },
            "final_score": final_score,
            "skills_verified_ratio": skill_ratio,
            "projects_verified_ratio": project_ratio,
            "experience_verified_ratio": experience_ratio,
            "linkedin_verified": linkedin_verified,
            "collaboration_detected": collaboration_signal,
        }

    # ── empty fallback ──────────────────────────────────────

    @staticmethod
    def _empty(username: str) -> Dict[str, Any]:
        return {
            "username": username,
            "raw_metrics": {
                "skill_ratio": 0.0,
                "skill_verified": 0,
                "skill_total": 0,
                "skill_mismatches": [],
                "project_ratio": 0.0,
                "project_verified": 0,
                "project_total": 0,
                "project_mismatches": [],
                "experience_ratio": 0.0,
                "experience_verified": 0,
                "experience_total": 0,
                "experience_mismatches": [],
                "earliest_github_repo_date": None,
                "linkedin_profile_verified": False,
                "linkedin_skill_mismatch": [],
                "linkedin_experience_mismatch": [],
                "multi_contributor_repos": 0,
            },
            "normalized_score": 0.0,
            "explanation": {
                "formula": "N/A — no GitHub data found",
                "components": {},
                "final_score": 0.0,
                "skills_verified_ratio": 0.0,
                "projects_verified_ratio": 0.0,
                "experience_verified_ratio": 0.0,
                "linkedin_verified": False,
                "collaboration_detected": False,
            },
        }
