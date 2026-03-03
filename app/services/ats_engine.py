"""ENGINE 8 — Advanced ATS Resume Intelligence Engine.

Production-grade resume intelligence system that:
  - Simulates ATS extraction
  - Scores structural quality
  - Scores semantic skill alignment
  - Detects keyword stuffing
  - Detects missing impact metrics
  - Evaluates readability
  - Cross-validates with GitHub + Product Mindset signals
  - Produces structured output for dashboard rendering

All scoring is deterministic (no randomness).
Score range: 0–100 for all sub-scores and the normalized final score.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import logger

# ── Contact extraction patterns ───────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}"
)
_LOCATION_RE = re.compile(
    r"(?:(?:based\s+in|located?\s+in|address|city)\s*[:\s]*)"
    r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?)",
    re.IGNORECASE,
)
_NAME_RE = re.compile(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})\s*$", re.MULTILINE)

# ── Section heading patterns ─────────────────────────────

_SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "contact": re.compile(
        r"^[#\s]*(?:contact|personal\s+(?:info|details|information)|address)\s*[:\-—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "summary": re.compile(
        r"^[#\s]*(?:summary|profile|objective|about\s+me|professional\s+summary)\s*[:\-—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "experience": re.compile(
        r"^[#\s]*(?:(?:professional\s+|work\s+)?experience|work\s+history|employment(?:\s+history)?)\s*[:\-—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "skills": re.compile(
        r"^[#\s]*(?:(?:technical\s+|core\s+|key\s+)?skills?|(?:technical\s+)?(?:proficiency|competencies?|expertise|technologies))\s*[:\-—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "education": re.compile(
        r"^[#\s]*(?:education|academic|qualifications?|degrees?)\s*[:\-—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "certifications": re.compile(
        r"^[#\s]*(?:certifications?|licenses?|credentials?|accreditations?)\s*[:\-—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "projects": re.compile(
        r"^[#\s]*(?:(?:personal\s+|academic\s+|key\s+|notable\s+)?projects?|portfolio)\s*[:\-—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}

_ANY_SECTION_RE = re.compile(
    r"^[#\s]*(?:experience|work|employment|projects?|portfolio|education|"
    r"academic|qualifications?|certifications?|skills?|proficiency|competencies?|"
    r"expertise|interests?|hobbies|references?|languages?|awards?|publications?|"
    r"achievements?|summary|objective|about|contact|personal|address|"
    r"technologies|volunteering|activities)\s*[:\-—]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# ── Date detection ────────────────────────────────────────

_MONTH_NAMES = (
    "january|february|march|april|may|june|july|august|september|"
    "october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
)

_DATE_RE = re.compile(
    rf"(?:{_MONTH_NAMES})\s*['']?\d{{2,4}}",
    re.IGNORECASE,
)

_DATE_RANGE_RE = re.compile(
    rf"(?P<start>(?:{_MONTH_NAMES})\s*['']?\d{{2,4}})"
    rf"\s*[-–—to]+\s*"
    rf"(?P<end>(?:{_MONTH_NAMES})\s*['']?\d{{2,4}}|present|current|now)",
    re.IGNORECASE,
)

_YEAR_RANGE_RE = re.compile(
    r"(?P<start>\d{4})\s*[-–—to]+\s*(?P<end>\d{4}|present|current|now)",
    re.IGNORECASE,
)

# ── Action verbs ──────────────────────────────────────────
_ACTION_VERBS = {
    "achieved", "administered", "advanced", "analyzed", "architected",
    "automated", "built", "collaborated", "configured", "consolidated",
    "contributed", "created", "decreased", "delivered", "deployed",
    "designed", "developed", "directed", "drove", "eliminated",
    "enabled", "engineered", "enhanced", "established", "executed",
    "expanded", "facilitated", "formulated", "generated", "guided",
    "identified", "implemented", "improved", "increased", "influenced",
    "initiated", "innovated", "integrated", "introduced", "launched",
    "led", "maintained", "managed", "mentored", "migrated",
    "modernized", "monitored", "negotiated", "operated", "optimized",
    "orchestrated", "organized", "overhauled", "partnered", "performed",
    "piloted", "pioneered", "planned", "presented", "prioritized",
    "produced", "programmed", "proposed", "prototyped", "provided",
    "published", "rebuilt", "reduced", "refactored", "reformed",
    "remodeled", "reorganized", "replaced", "resolved", "restructured",
    "revamped", "reviewed", "scaled", "secured", "shipped",
    "simplified", "solved", "spearheaded", "standardized", "streamlined",
    "strengthened", "supervised", "supported", "surpassed", "tested",
    "trained", "transformed", "troubleshot", "unified", "upgraded",
    "utilized", "validated", "visualized", "wrote",
}

# ── Passive voice indicators ─────────────────────────────
_PASSIVE_RE = re.compile(
    r"\b(?:was|were|been|being|is|are|am)\s+\w+(?:ed|en|t)\b",
    re.IGNORECASE,
)

# ── Impact/metric patterns ───────────────────────────────
_METRIC_RE = re.compile(
    r"(?:\d+[%+xX]|\$\d+|\d+\s*(?:percent|users?|clients?|customers?|"
    r"requests?|transactions?|queries|records?|team\s*members?|engineers?|"
    r"developers?|people|employees|months?|years?|times?)|\d+[kKmMbB]\+?)",
    re.IGNORECASE,
)

# ── Leadership/senior keywords ───────────────────────────
_LEADERSHIP_KEYWORDS = {
    "led", "managed", "mentored", "directed", "supervised",
    "oversaw", "coordinated", "spearheaded", "headed",
    "ownership", "responsible for", "accountable",
}

_SYSTEM_DESIGN_KEYWORDS = {
    "architecture", "system design", "microservice", "distributed",
    "scalable", "high availability", "load balancing", "caching",
    "message queue", "event driven", "domain driven", "ddd",
    "infrastructure", "terraform", "kubernetes", "orchestration",
    "service mesh", "api gateway",
}

_CROSS_TEAM_KEYWORDS = {
    "cross-functional", "cross-team", "stakeholder", "product manager",
    "collaborated with", "partnered with", "interfaced with",
    "alignment", "roadmap", "strategy",
}

# ── Tech skill sets for authenticity ──────────────────────
_KNOWN_TECH_SKILLS: Set[str] = {
    "python", "javascript", "typescript", "java", "c++", "c#", "c",
    "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
    "r", "sql", "html", "css", "bash", "shell", "graphql",
    "react", "angular", "vue", "svelte", "next.js", "nextjs", "nuxt",
    "node.js", "nodejs", "express", "fastapi", "flask", "django",
    "spring", "spring boot", "rails", "laravel",
    "flutter", "react native",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "jenkins", "github actions", "gitlab ci", "circleci",
    "kafka", "rabbitmq", "celery",
    "git", "linux", "nginx",
    "jest", "pytest", "selenium", "cypress",
    "figma", "jira",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data science", "data engineering",
    "ci/cd", "devops", "agile", "scrum",
    ".net", "asp.net",
}

_BUZZWORDS: Set[str] = {
    "synergy", "leverage", "paradigm", "disruptive", "innovative",
    "cutting-edge", "next-generation", "world-class", "best-in-class",
    "rockstar", "ninja", "guru", "wizard", "unicorn",
    "thought leader", "game-changer", "bleeding edge", "revolutionary",
    "proactive", "dynamic", "self-starter", "go-getter",
    "passionate", "detail-oriented", "team player", "results-driven",
    "fast-paced", "hard-working", "motivated",
}


def _extract_section_text(
    full_text: str,
    section_re: re.Pattern,
    all_section_re: re.Pattern,
) -> str:
    """Extract text between a section header and the next section header."""
    match = section_re.search(full_text)
    if not match:
        return ""
    start = match.end()
    next_match = all_section_re.search(full_text, start)
    end = next_match.start() if next_match else len(full_text)
    return full_text[start:end].strip()


def _extract_bullets(text: str) -> List[str]:
    """Extract bullet points from text block."""
    bullets: List[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Match lines starting with bullet chars or dashes
        if re.match(r"^[•◦▸▹\-–—\*►⚫⬥]\s+", stripped):
            bullets.append(re.sub(r"^[•◦▸▹\-–—\*►⚫⬥]\s+", "", stripped))
        elif re.match(r"^\d+[.)]\s+", stripped):
            bullets.append(re.sub(r"^\d+[.)]\s+", "", stripped))
        elif len(stripped) > 20 and not stripped.endswith(":"):
            # Standalone content lines in experience sections
            bullets.append(stripped)
    return [b for b in bullets if len(b) > 5]


class ATSIntelligenceEngine:
    """Advanced ATS Resume Intelligence Engine.

    Deterministic, resilient, run_id-isolated.
    Produces structured output for dashboard rendering.
    """

    # ── Public API ────────────────────────────────────────

    async def analyze(
        self,
        username: str,
        resume_text: str,
        *,
        role_level: str = "mid",
        github_languages: Optional[List[str]] = None,
        github_repos: Optional[List[Dict[str, Any]]] = None,
        github_total_commits: int = 0,
        product_mindset_score: float = 0.0,
        github_score: float = 0.0,
    ) -> Dict[str, Any]:
        """Run the full ATS intelligence pipeline.

        Returns a structured dict matching the engine contract.
        """
        logger.info(f"[ATS] Starting ATS intelligence analysis for {username}")

        if not resume_text or len(resume_text.strip()) < 20:
            logger.warning(f"[ATS] Resume text too short or missing for {username}")
            return self._failed("Resume text is empty or too short")

        try:
            text = self._normalize_text(resume_text)

            # Phase 2: ATS Parser Simulation
            parsed = self._simulate_ats_parse(text)
            parse_score = self._compute_parse_score(parsed, text)

            # Phase 3: Structural Quality Analysis
            structure_analysis = self._analyze_structure(text, parsed)
            structure_score = structure_analysis["score"]

            # Phase 4: Semantic Skill Matching
            skill_analysis = self._analyze_skill_authenticity(
                parsed, text,
                github_languages=github_languages or [],
                github_repos=github_repos or [],
            )
            skill_authenticity_score = skill_analysis["score"]

            # Phase 5: Job Role Alignment
            role_analysis = self._analyze_role_alignment(
                text, parsed, role_level
            )
            role_alignment_score = role_analysis["score"]

            # Phase 6: Keyword Stuffing Detection
            stuffing_analysis = self._detect_keyword_stuffing(
                text, parsed,
                github_languages=github_languages or [],
                github_repos=github_repos or [],
            )
            keyword_stuffing_risk = stuffing_analysis["risk"]

            # Phase 7: Readability & Recruiter Experience
            readability_analysis = self._analyze_readability(text)
            recruiter_readability = readability_analysis["classification"]

            # Phase 8: Career Progression Logic Check
            career_analysis = self._analyze_career_progression(parsed)
            career_consistency_score = career_analysis["score"]

            # Phase 9: Cross-Engine Validation
            cross_validation = self._cross_validate(
                text, parsed, role_level,
                github_total_commits=github_total_commits,
                github_score=github_score,
                product_mindset_score=product_mindset_score,
                github_repos=github_repos or [],
            )
            cross_validation_penalty = cross_validation["penalty"]

            # Phase 10: Final Score
            raw_score = self._compute_final_score(
                parse_score=parse_score,
                structure_score=structure_score,
                skill_authenticity_score=skill_authenticity_score,
                role_alignment_score=role_alignment_score,
                career_consistency_score=career_consistency_score,
                readability_analysis=readability_analysis,
                stuffing_analysis=stuffing_analysis,
            )

            normalized_score = round(
                max(0.0, min(100.0, raw_score - cross_validation_penalty)), 2
            )

            raw_metrics = {
                "parse_score": parse_score,
                "structure_score": structure_score,
                "skill_authenticity_score": skill_authenticity_score,
                "role_alignment_score": role_alignment_score,
                "career_consistency_score": career_consistency_score,
                "keyword_stuffing_risk": keyword_stuffing_risk,
                "recruiter_readability": recruiter_readability,
                "cross_validation_penalty": cross_validation_penalty,
                "parsed_resume": {
                    "name": parsed["name"],
                    "email": parsed["email"],
                    "phone": parsed["phone"],
                    "skills_count": len(parsed["skills"]),
                    "experience_count": len(parsed["experience"]),
                    "education_count": len(parsed["education"]),
                    "certifications_count": len(parsed["certifications"]),
                },
                "structure_detail": structure_analysis["detail"],
                "skill_detail": skill_analysis["detail"],
                "role_detail": role_analysis["detail"],
                "stuffing_detail": stuffing_analysis["detail"],
                "readability_detail": readability_analysis["detail"],
                "career_detail": career_analysis["detail"],
                "cross_validation_detail": cross_validation["detail"],
                "warnings": self._collect_warnings(
                    structure_analysis, skill_analysis, stuffing_analysis,
                    readability_analysis, career_analysis, cross_validation,
                ),
            }

            explanation = {
                "parse_quality": f"ATS parse score: {parse_score}/100",
                "structure": structure_analysis["explanation"],
                "skills": skill_analysis["explanation"],
                "role_alignment": role_analysis["explanation"],
                "keyword_stuffing": stuffing_analysis["explanation"],
                "readability": readability_analysis["explanation"],
                "career": career_analysis["explanation"],
                "cross_validation": cross_validation["explanation"],
                "final_score": f"Weighted score {raw_score:.1f} - penalty {cross_validation_penalty:.1f} = {normalized_score:.1f}",
            }

            logger.info(
                f"[ATS] Analysis complete for {username}: "
                f"score={normalized_score}, parse={parse_score}, "
                f"structure={structure_score}, skill_auth={skill_authenticity_score}"
            )

            return {
                "username": username,
                "normalized_score": normalized_score,
                "structure_score": structure_score,
                "parse_score": parse_score,
                "skill_authenticity_score": skill_authenticity_score,
                "role_alignment_score": role_alignment_score,
                "career_consistency_score": career_consistency_score,
                "keyword_stuffing_risk": keyword_stuffing_risk,
                "recruiter_readability": recruiter_readability,
                "cross_validation_penalty": cross_validation_penalty,
                "raw_metrics": raw_metrics,
                "explanation": explanation,
                "engine_failed": False,
                "failure_reason": None,
                "rate_limited": False,
            }

        except Exception as exc:
            logger.exception(f"[ATS] Engine failed for {username}: {exc}")
            return self._failed(str(exc))

    # ── Phase 1: Text Normalization ───────────────────────

    def _normalize_text(self, text: str) -> str:
        """Normalize resume text: collapse whitespace, preserve structure."""
        # Remove null bytes and non-printable chars
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        # Collapse multiple spaces to single
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse more than 3 consecutive newlines to 2
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    # ── Phase 2: ATS Parser Simulation ────────────────────

    def _simulate_ats_parse(self, text: str) -> Dict[str, Any]:
        """Simulate ATS extraction of structured resume data."""
        # Extract contact info
        emails = _EMAIL_RE.findall(text)
        phones = _PHONE_RE.findall(text)
        locations = _LOCATION_RE.findall(text)
        names = _NAME_RE.findall(text[:500])  # Name usually in first 500 chars

        # Extract section texts
        skills_text = _extract_section_text(
            text, _SECTION_PATTERNS["skills"], _ANY_SECTION_RE
        )
        experience_text = _extract_section_text(
            text, _SECTION_PATTERNS["experience"], _ANY_SECTION_RE
        )
        education_text = _extract_section_text(
            text, _SECTION_PATTERNS["education"], _ANY_SECTION_RE
        )
        cert_text = _extract_section_text(
            text, _SECTION_PATTERNS["certifications"], _ANY_SECTION_RE
        )

        # Parse skills
        skills = self._extract_skills_from_section(skills_text or text)

        # Parse experience blocks
        experience = self._parse_experience_blocks(experience_text)

        # Parse education
        education = self._parse_education(education_text)

        # Parse certifications
        certifications = self._parse_certifications(cert_text)

        return {
            "name": names[0] if names else None,
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
            "location": locations[0] if locations else None,
            "skills": skills,
            "experience": experience,
            "education": education,
            "certifications": certifications,
            "sections_found": [
                s for s, p in _SECTION_PATTERNS.items()
                if p.search(text)
            ],
        }

    def _extract_skills_from_section(self, text: str) -> List[str]:
        """Extract individual skills from a skills section or full text."""
        text_lower = text.lower()
        found: List[str] = []

        for skill in sorted(_KNOWN_TECH_SKILLS, key=len, reverse=True):
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found.append(skill)

        return list(dict.fromkeys(found))  # dedupe preserving order

    def _parse_experience_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Parse experience section into structured blocks."""
        if not text:
            return []

        blocks: List[Dict[str, Any]] = []
        lines = text.split("\n")

        current_block: Optional[Dict[str, Any]] = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check for date range — signals new block
            date_match = _DATE_RANGE_RE.search(stripped) or _YEAR_RANGE_RE.search(stripped)
            if date_match:
                if current_block:
                    blocks.append(current_block)

                # Extract title/company from the line (heuristic)
                before_date = stripped[:date_match.start()].strip().rstrip("|–—-,")
                parts = re.split(r"\s*[|–—@,]\s*", before_date)

                current_block = {
                    "title": parts[0].strip() if parts else None,
                    "company": parts[1].strip() if len(parts) > 1 else None,
                    "start_date": date_match.group("start"),
                    "end_date": date_match.group("end"),
                    "bullet_points": [],
                }
                continue

            # Accumulate bullet points
            if current_block is not None:
                if re.match(r"^[•◦▸▹\-–—\*►]\s+", stripped) or re.match(r"^\d+[.)]\s+", stripped):
                    bullet = re.sub(r"^[•◦▸▹\-–—\*►]\s+", "", stripped)
                    bullet = re.sub(r"^\d+[.)]\s+", "", bullet)
                    current_block["bullet_points"].append(bullet)
                elif len(stripped) > 25 and not stripped.endswith(":"):
                    current_block["bullet_points"].append(stripped)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _parse_education(self, text: str) -> List[str]:
        """Parse education section into entries."""
        if not text:
            return []
        entries: List[str] = []
        for line in text.split("\n"):
            stripped = line.strip()
            if len(stripped) > 10 and not stripped.endswith(":"):
                entries.append(stripped)
        return entries[:10]

    def _parse_certifications(self, text: str) -> List[str]:
        """Parse certifications section."""
        if not text:
            return []
        entries: List[str] = []
        for line in text.split("\n"):
            stripped = line.strip()
            if len(stripped) > 5:
                cleaned = re.sub(r"^[•◦▸▹\-–—\*►]\s+", "", stripped)
                if cleaned:
                    entries.append(cleaned)
        return entries[:20]

    def _compute_parse_score(self, parsed: Dict[str, Any], text: str) -> float:
        """Compute ATS parse quality score (0–100)."""
        score = 0.0

        # Contact extraction (25 pts)
        if parsed["name"]:
            score += 8
        if parsed["email"]:
            score += 8
        if parsed["phone"]:
            score += 5
        if parsed["location"]:
            score += 4

        # Section clarity (30 pts)
        sections_found = parsed["sections_found"]
        section_score = min(30, len(sections_found) * 6)
        score += section_score

        # Date format consistency (15 pts)
        dates_found = _DATE_RE.findall(text)
        if len(dates_found) >= 2:
            score += 15
        elif len(dates_found) >= 1:
            score += 8

        # Header recognition confidence (15 pts)
        if len(sections_found) >= 4:
            score += 15
        elif len(sections_found) >= 3:
            score += 10
        elif len(sections_found) >= 2:
            score += 5

        # Experience & skills extraction (15 pts)
        if parsed["experience"]:
            score += 8
        if parsed["skills"]:
            score += 7

        return round(min(100.0, score), 2)

    # ── Phase 3: Structural Quality Analysis ──────────────

    def _analyze_structure(
        self, text: str, parsed: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze structural quality of the resume."""
        detail: Dict[str, Any] = {}
        warnings: List[str] = []
        score = 0.0

        # 1. Section completeness (30 pts)
        sections = parsed["sections_found"]
        required = {"experience", "skills", "education"}
        recommended = {"summary", "contact", "projects"}
        found_required = required.intersection(sections)
        found_recommended = recommended.intersection(sections)

        section_completeness = (len(found_required) / max(len(required), 1)) * 20
        section_completeness += (len(found_recommended) / max(len(recommended), 1)) * 10
        score += section_completeness
        detail["sections_found"] = sections
        detail["sections_missing"] = list(required - set(sections))
        detail["section_completeness"] = round(section_completeness / 30.0, 3)  # normalize to 0-1

        if "experience" not in sections:
            warnings.append("Missing Experience section")
        if "skills" not in sections:
            warnings.append("Missing Skills section")
        if "education" not in sections:
            warnings.append("Missing Education section")

        # 2. Bullet quality (30 pts)
        all_bullets = []
        for exp in parsed["experience"]:
            all_bullets.extend(exp.get("bullet_points", []))

        if all_bullets:
            avg_bullet_len = sum(len(b) for b in all_bullets) / len(all_bullets)
            detail["avg_bullet_length"] = round(avg_bullet_len, 1)
            detail["total_bullets"] = len(all_bullets)

            # Bullet length score (10 pts) — ideal 50-150 chars
            if 50 <= avg_bullet_len <= 150:
                score += 10
            elif 30 <= avg_bullet_len <= 200:
                score += 6
            else:
                score += 2
                if avg_bullet_len < 30:
                    warnings.append("Bullet points too short — lacks detail")

            # Verb-led bullets (10 pts)
            verb_led = sum(
                1 for b in all_bullets
                if b.split()[0].lower().rstrip("ed,ing,s") in _ACTION_VERBS
                or b.split()[0].lower() in _ACTION_VERBS
            )
            verb_ratio = verb_led / max(len(all_bullets), 1)
            detail["verb_led_ratio"] = round(verb_ratio, 3)
            score += verb_ratio * 10

            # Active vs passive voice (10 pts)
            passive_count = sum(
                1 for b in all_bullets if _PASSIVE_RE.search(b)
            )
            passive_ratio = passive_count / max(len(all_bullets), 1)
            detail["passive_voice_ratio"] = round(passive_ratio, 3)
            active_score = (1 - passive_ratio) * 10
            score += active_score

            # Compute bullet quality as combined score of verb_led + active voice + length (0-1)
            bullet_quality = (verb_ratio * 0.4) + ((1 - passive_ratio) * 0.3)
            # Add bullet length quality contribution
            if 50 <= avg_bullet_len <= 150:
                bullet_quality += 0.3
            elif 30 <= avg_bullet_len <= 200:
                bullet_quality += 0.18
            else:
                bullet_quality += 0.06
            detail["bullet_quality"] = round(min(1.0, bullet_quality), 3)

            if passive_ratio > 0.4:
                warnings.append("High passive voice usage — use active verbs")
        else:
            detail["avg_bullet_length"] = 0
            detail["total_bullets"] = 0
            detail["verb_led_ratio"] = 0
            detail["passive_voice_ratio"] = 0
            detail["bullet_quality"] = 0
            score += 5  # some credit for having text
            warnings.append("No bullet points detected in experience")

        # 3. Metric density (20 pts)
        if all_bullets:
            metric_bullets = sum(
                1 for b in all_bullets if _METRIC_RE.search(b)
            )
            metric_density = metric_bullets / max(len(all_bullets), 1)
            detail["metric_density"] = round(metric_density, 3)
            detail["metric_bullets_count"] = metric_bullets
            score += metric_density * 20

            if metric_density < 0.2:
                warnings.append("Low impact metrics — add quantifiable results")
        else:
            detail["metric_density"] = 0
            detail["metric_bullets_count"] = 0

        # 4. Formatting safety (20 pts)
        formatting_score = 20.0
        text_lower = text.lower()

        # Table detection
        has_tables = bool(re.search(r"[│┃┆┇┊┋╎╏║]", text)) or text.count("\t") > 10
        detail["has_tables"] = has_tables
        if has_tables:
            formatting_score -= 5
            warnings.append("Tables detected — may cause ATS parsing issues")

        # Column detection (multiple spaces mid-line)
        column_lines = sum(
            1 for line in text.split("\n")
            if len(re.findall(r"  {3,}", line)) >= 1 and len(line) > 40
        )
        has_columns = column_lines > 5
        detail["has_columns"] = has_columns
        if has_columns:
            formatting_score -= 5
            warnings.append("Multi-column layout detected — ATS may misread")

        # Very short text = possibly image-based
        word_count = len(text.split())
        detail["word_count"] = word_count
        if word_count < 100:
            formatting_score -= 10
            warnings.append("Very low word count — possible image-based PDF")

        score += max(0, formatting_score)
        detail["formatting_safety"] = round(max(0, formatting_score) / 20.0, 3)  # normalize to 0-1

        final_score = round(max(0.0, min(100.0, score)), 2)

        return {
            "score": final_score,
            "detail": detail,
            "warnings": warnings,
            "explanation": (
                f"Structure score {final_score}/100: "
                f"{len(sections)} sections found, "
                f"{len(all_bullets)} bullets, "
                f"{detail.get('metric_density', 0) * 100:.0f}% with metrics"
            ),
        }

    # ── Phase 4: Semantic Skill Matching ──────────────────

    def _analyze_skill_authenticity(
        self,
        parsed: Dict[str, Any],
        text: str,
        *,
        github_languages: List[str],
        github_repos: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Score skill authenticity using resume ↔ GitHub alignment."""
        detail: Dict[str, Any] = {}
        warnings: List[str] = []

        resume_skills = {s.lower() for s in parsed["skills"]}
        github_langs = {l.lower() for l in github_languages}

        # Build GitHub tech signals from repos
        github_tech: Set[str] = set(github_langs)
        for repo in github_repos:
            lang = (repo.get("language") or "").lower()
            if lang:
                github_tech.add(lang)
            for topic in (repo.get("topics") or []):
                github_tech.add(topic.lower())
            desc = (repo.get("description") or "").lower()
            for skill in _KNOWN_TECH_SKILLS:
                if skill in desc:
                    github_tech.add(skill)

        detail["resume_skills_count"] = len(resume_skills)
        detail["github_tech_signals"] = len(github_tech)

        # Skill overlap ratio (40 pts)
        if resume_skills and github_tech:
            overlap = resume_skills.intersection(github_tech)
            overlap_ratio = len(overlap) / max(len(resume_skills), 1)
            detail["overlap_count"] = len(overlap)
            detail["overlap_ratio"] = round(overlap_ratio, 3)
            overlap_score = overlap_ratio * 40
        elif not github_tech:
            # No GitHub data — neutral
            overlap_ratio = 0.5
            detail["overlap_count"] = 0
            detail["overlap_ratio"] = 0.5
            overlap_score = 20  # neutral
        else:
            overlap_ratio = 0
            detail["overlap_count"] = 0
            detail["overlap_ratio"] = 0
            overlap_score = 0

        # Skill inflation detection (30 pts)
        claimed_not_verified = resume_skills - github_tech if github_tech else set()
        inflation_ratio = (
            len(claimed_not_verified) / max(len(resume_skills), 1)
            if resume_skills else 0
        )
        detail["unverified_skills"] = list(claimed_not_verified)[:15]
        detail["inflation_ratio"] = round(inflation_ratio, 3)

        if inflation_ratio > 0.7 and github_tech:
            inflation_score = 5
            warnings.append("High skill inflation — many claimed skills not found in GitHub")
        elif inflation_ratio > 0.5 and github_tech:
            inflation_score = 15
        else:
            inflation_score = 30

        # Buzzword density (30 pts)
        text_lower = text.lower()
        buzzword_count = sum(1 for b in _BUZZWORDS if b in text_lower)
        word_count = max(len(text.split()), 1)
        buzzword_density = buzzword_count / word_count * 100
        detail["buzzword_count"] = buzzword_count
        detail["buzzword_density_pct"] = round(buzzword_density, 3)

        if buzzword_density > 2.0:
            buzzword_score = 5
            warnings.append("High buzzword density — reduce subjective claims")
        elif buzzword_density > 1.0:
            buzzword_score = 15
        else:
            buzzword_score = 30

        score = round(max(0.0, min(100.0, overlap_score + inflation_score + buzzword_score)), 2)

        return {
            "score": score,
            "detail": detail,
            "warnings": warnings,
            "explanation": (
                f"Skill authenticity {score}/100: "
                f"{detail['overlap_count']} of {len(resume_skills)} skills verified via GitHub, "
                f"inflation ratio {inflation_ratio:.0%}, "
                f"buzzword density {buzzword_density:.2f}%"
            ),
        }

    # ── Phase 5: Job Role Alignment ───────────────────────

    def _analyze_role_alignment(
        self,
        text: str,
        parsed: Dict[str, Any],
        role_level: str,
    ) -> Dict[str, Any]:
        """Score alignment between resume content and target role level."""
        detail: Dict[str, Any] = {}
        warnings: List[str] = []
        text_lower = text.lower()

        all_bullets = []
        for exp in parsed["experience"]:
            all_bullets.extend(exp.get("bullet_points", []))

        score = 0.0

        if role_level == "entry":
            # Education presence (30 pts)
            has_education = bool(parsed["education"])
            detail["has_education"] = has_education
            score += 30 if has_education else 5

            # Internship signals (30 pts)
            intern_keywords = ["intern", "internship", "trainee", "apprentice", "co-op"]
            has_internship = any(kw in text_lower for kw in intern_keywords)
            detail["has_internship"] = has_internship
            score += 30 if has_internship else 10

            # Technical project density (40 pts)
            project_count = len(parsed.get("experience", []))
            has_projects = "projects" in parsed["sections_found"]
            detail["project_density"] = project_count
            detail["has_projects_section"] = has_projects

            project_score = min(40, project_count * 8 + (15 if has_projects else 0))
            score += project_score

        elif role_level == "senior":
            # System design keywords (30 pts)
            sd_matches = sum(1 for kw in _SYSTEM_DESIGN_KEYWORDS if kw in text_lower)
            detail["system_design_matches"] = sd_matches
            sd_score = min(30, sd_matches * 6)
            score += sd_score

            if sd_matches < 2:
                warnings.append("Few system design references for senior role")

            # Cross-team collaboration (25 pts)
            ct_matches = sum(1 for kw in _CROSS_TEAM_KEYWORDS if kw in text_lower)
            detail["cross_team_matches"] = ct_matches
            ct_score = min(25, ct_matches * 5)
            score += ct_score

            # Leadership verbs (25 pts)
            leadership_found = sum(
                1 for b in all_bullets
                if any(kw in b.lower() for kw in _LEADERSHIP_KEYWORDS)
            )
            detail["leadership_bullets"] = leadership_found
            lead_score = min(25, leadership_found * 5)
            score += lead_score

            if leadership_found < 3:
                warnings.append("Low leadership signal for senior role")

            # Impact metrics for senior (20 pts)
            metric_bullets = sum(1 for b in all_bullets if _METRIC_RE.search(b))
            detail["senior_metric_bullets"] = metric_bullets
            score += min(20, metric_bullets * 4)

        else:  # mid
            # Impact metrics (30 pts)
            metric_bullets = sum(1 for b in all_bullets if _METRIC_RE.search(b))
            detail["metric_bullets"] = metric_bullets
            score += min(30, metric_bullets * 5)

            # Ownership signals (30 pts)
            ownership_keywords = [
                "owned", "ownership", "responsible", "lead", "drove",
                "initiated", "spearheaded", "managed", "delivered",
            ]
            ownership_count = sum(
                1 for b in all_bullets
                if any(kw in b.lower() for kw in ownership_keywords)
            )
            detail["ownership_signals"] = ownership_count
            score += min(30, ownership_count * 6)

            # Leadership verbs (20 pts)
            leadership_found = sum(
                1 for b in all_bullets
                if any(kw in b.lower() for kw in _LEADERSHIP_KEYWORDS)
            )
            detail["leadership_bullets"] = leadership_found
            score += min(20, leadership_found * 5)

            # Technical depth (20 pts)
            tech_depth = len(parsed["skills"])
            detail["tech_skill_count"] = tech_depth
            score += min(20, tech_depth * 2)

        final_score = round(max(0.0, min(100.0, score)), 2)

        return {
            "score": final_score,
            "detail": detail,
            "warnings": warnings,
            "explanation": (
                f"Role alignment ({role_level}) score {final_score}/100"
            ),
        }

    # ── Phase 6: Keyword Stuffing Detection ───────────────

    def _detect_keyword_stuffing(
        self,
        text: str,
        parsed: Dict[str, Any],
        *,
        github_languages: List[str],
        github_repos: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Detect keyword stuffing patterns."""
        detail: Dict[str, Any] = {}
        warnings: List[str] = []
        risk_score = 0

        text_lower = text.lower()
        words = re.findall(r"\b[a-z]{3,}\b", text_lower)
        word_count = max(len(words), 1)

        # 1. Excessive repeated keywords
        word_freq = Counter(words)
        most_common = word_freq.most_common(10)
        # Filter out common English words
        stop_words = {
            "the", "and", "for", "with", "that", "this", "from",
            "have", "has", "was", "were", "are", "been", "will",
            "can", "our", "not", "but", "they", "your", "all",
            "their", "which", "when", "would", "there", "been",
        }
        tech_repeats = [
            (w, c) for w, c in most_common
            if w not in stop_words and c > 5
        ]
        detail["top_repeated_words"] = tech_repeats[:5]

        if tech_repeats:
            max_repeat = tech_repeats[0][1]
            if max_repeat > 15:
                risk_score += 35
                warnings.append(f'"{tech_repeats[0][0]}" repeated {max_repeat} times')
            elif max_repeat > 10:
                risk_score += 20

        # 2. Long comma-separated skill lists
        skills_text = _extract_section_text(
            text, _SECTION_PATTERNS["skills"], _ANY_SECTION_RE
        )
        if skills_text:
            comma_items = skills_text.count(",")
            lines_count = max(skills_text.count("\n") + 1, 1)
            comma_density = comma_items / lines_count
            detail["skills_comma_density"] = round(comma_density, 2)

            if comma_items > 40:
                risk_score += 25
                warnings.append("Excessive comma-separated skill list")
            elif comma_items > 25:
                risk_score += 10

        # 3. High TF-IDF spike for single term
        if word_count > 50:
            max_tf = max(c for _, c in word_freq.most_common(5) if _ not in stop_words) if word_freq else 0
            tf_ratio = max_tf / word_count
            detail["max_tf_ratio"] = round(tf_ratio, 4)
            if tf_ratio > 0.05:
                risk_score += 20
                warnings.append("Single term dominates document — possible keyword stuffing")

        # 4. Skills not found in GitHub codebase
        github_tech: Set[str] = set()
        for l in github_languages:
            github_tech.add(l.lower())
        for repo in github_repos:
            lang = (repo.get("language") or "").lower()
            if lang:
                github_tech.add(lang)
            for topic in (repo.get("topics") or []):
                github_tech.add(topic.lower())

        resume_skills = {s.lower() for s in parsed["skills"]}
        if github_tech and resume_skills:
            phantom = resume_skills - github_tech
            phantom_ratio = len(phantom) / max(len(resume_skills), 1)
            detail["phantom_skills"] = list(phantom)[:10]
            detail["phantom_ratio"] = round(phantom_ratio, 3)

            if phantom_ratio > 0.7:
                risk_score += 20
                warnings.append("Most listed skills not found in GitHub repos")
            elif phantom_ratio > 0.5:
                risk_score += 10

        # Classify risk
        if risk_score >= 50:
            risk = "High"
        elif risk_score >= 25:
            risk = "Medium"
        else:
            risk = "Low"

        detail["risk_score_raw"] = risk_score

        return {
            "risk": risk,
            "detail": detail,
            "warnings": warnings,
            "explanation": f"Keyword stuffing risk: {risk} (raw score {risk_score})",
        }

    # ── Phase 7: Readability & Recruiter Experience ───────

    def _analyze_readability(self, text: str) -> Dict[str, Any]:
        """Compute readability metrics."""
        detail: Dict[str, Any] = {}
        warnings: List[str] = []

        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        words = text.split()
        word_count = max(len(words), 1)
        sentence_count = max(len(sentences), 1)

        # Average sentence length
        avg_sentence_len = word_count / sentence_count
        detail["avg_sentence_length"] = round(avg_sentence_len, 1)

        # Syllable count approximation
        def count_syllables(word: str) -> int:
            word = word.lower().strip(".,;:!?")
            if len(word) <= 3:
                return 1
            count = len(re.findall(r"[aeiouy]+", word))
            if word.endswith("e") and not word.endswith("le"):
                count -= 1
            return max(1, count)

        total_syllables = sum(count_syllables(w) for w in words)
        avg_syllables = total_syllables / word_count

        # Flesch Reading Ease (adapted for resumes — standard formula)
        flesch = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables)
        flesch = max(0, min(100, flesch))
        detail["flesch_reading_ease"] = round(flesch, 1)

        # Paragraph density
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        detail["paragraph_count"] = len(paragraphs)
        avg_para_len = word_count / max(len(paragraphs), 1)
        detail["avg_paragraph_length"] = round(avg_para_len, 1)

        # Jargon overload
        jargon_count = sum(1 for w in words if len(w) > 12 and not w.startswith("http"))
        jargon_ratio = jargon_count / word_count
        detail["jargon_ratio"] = round(jargon_ratio, 4)

        # Classify readability
        readability_score = 0.0

        # Flesch score contribution (40 pts)
        if flesch >= 60:
            readability_score += 40
        elif flesch >= 40:
            readability_score += 25
        elif flesch >= 20:
            readability_score += 15
        else:
            readability_score += 5
            warnings.append("Very low readability — simplify language")

        # Sentence length contribution (30 pts)
        if 10 <= avg_sentence_len <= 25:
            readability_score += 30
        elif avg_sentence_len <= 35:
            readability_score += 20
        else:
            readability_score += 5
            warnings.append("Sentences too long — recruiter may skim past")

        # Jargon contribution (30 pts)
        if jargon_ratio < 0.05:
            readability_score += 30
        elif jargon_ratio < 0.10:
            readability_score += 20
        else:
            readability_score += 5
            warnings.append("Jargon overload — too many long technical terms")

        # Classify
        if readability_score >= 80:
            classification = "Excellent"
        elif readability_score >= 60:
            classification = "Good"
        elif readability_score >= 40:
            classification = "Dense"
        else:
            classification = "Overloaded"

        detail["readability_score"] = round(readability_score, 2)

        return {
            "classification": classification,
            "detail": detail,
            "warnings": warnings,
            "score": round(readability_score, 2),
            "explanation": (
                f"Recruiter readability: {classification} "
                f"(Flesch {flesch:.0f}, avg sentence {avg_sentence_len:.0f} words)"
            ),
        }

    # ── Phase 8: Career Progression Logic Check ───────────

    def _analyze_career_progression(
        self, parsed: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate career timeline consistency."""
        detail: Dict[str, Any] = {}
        warnings: List[str] = []
        score = 100.0  # Start perfect, deduct for issues

        experience = parsed["experience"]

        if not experience:
            detail["experience_count"] = 0
            return {
                "score": 50.0,
                "detail": detail,
                "warnings": ["No experience blocks found"],
                "explanation": "Career consistency: 50/100 (no experience data)",
            }

        detail["experience_count"] = len(experience)

        # Parse dates for analysis
        dated_blocks: List[Tuple[Optional[str], Optional[str], Dict]] = []
        for exp in experience:
            dated_blocks.append((exp.get("start_date"), exp.get("end_date"), exp))

        # 1. Timeline continuity & gap detection (-20 max)
        gaps_detected = 0
        total_months = 0
        for i, (start, end, _) in enumerate(dated_blocks):
            if start and end:
                sy = self._extract_year(start)
                ey = self._extract_year(end)
                if sy and ey:
                    months = max(0, (ey - sy)) * 12
                    total_months += months

                    # Check gap with next block
                    if i + 1 < len(dated_blocks):
                        next_start = dated_blocks[i + 1][0]
                        if next_start:
                            nsy = self._extract_year(next_start)
                            if nsy and ey and nsy > ey + 1:
                                gaps_detected += 1

        detail["gaps_detected"] = gaps_detected
        if gaps_detected > 2:
            score -= 20
            warnings.append(f"{gaps_detected} career gaps detected")
        elif gaps_detected > 0:
            score -= gaps_detected * 7

        # 2. Overlapping jobs detection (-15 max)
        overlaps = 0
        for i in range(len(dated_blocks)):
            for j in range(i + 1, len(dated_blocks)):
                s1, e1, _ = dated_blocks[i]
                s2, e2, _ = dated_blocks[j]
                sy1 = self._extract_year(s1) if s1 else None
                ey1 = self._extract_year(e1) if e1 else None
                sy2 = self._extract_year(s2) if s2 else None
                ey2 = self._extract_year(e2) if e2 else None

                if sy1 and ey1 and sy2 and ey2:
                    if sy1 <= ey2 and sy2 <= ey1:
                        overlaps += 1

        detail["overlapping_jobs"] = overlaps
        if overlaps > 1:
            score -= 15
            warnings.append("Multiple overlapping job periods")
        elif overlaps == 1:
            score -= 5  # Could be legitimate transition

        # 3. Unrealistic rapid promotions (-10 max)
        titles = [exp.get("title", "") for exp in experience if exp.get("title")]
        seniority_keywords = {
            "intern": 0, "junior": 1, "associate": 1, "trainee": 0,
            "mid": 2, "software engineer": 2, "developer": 2, "engineer": 2,
            "senior": 3, "lead": 4, "principal": 4, "staff": 4,
            "manager": 5, "director": 5, "vp": 6, "cto": 7, "ceo": 7,
        }
        levels: List[int] = []
        for title in titles:
            t_lower = title.lower()
            for kw, level in sorted(seniority_keywords.items(), key=lambda x: -len(x[0])):
                if kw in t_lower:
                    levels.append(level)
                    break

        rapid_jumps = 0
        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] >= 3:
                rapid_jumps += 1

        detail["rapid_promotions"] = rapid_jumps
        if rapid_jumps > 0:
            score -= min(10, rapid_jumps * 5)
            warnings.append("Unrealistically rapid career progression")

        # 4. Tenure stability index (-15 max)
        tenures: List[int] = []
        for start, end, _ in dated_blocks:
            sy = self._extract_year(start) if start else None
            ey = self._extract_year(end) if end else None
            if sy and ey and ey >= sy:
                tenures.append(ey - sy)

        if tenures:
            avg_tenure = sum(tenures) / len(tenures)
            detail["avg_tenure_years"] = round(avg_tenure, 1)
            short_tenures = sum(1 for t in tenures if t < 1)
            detail["short_tenure_count"] = short_tenures

            if short_tenures > 2:
                score -= 15
                warnings.append("Multiple short-tenure positions — retention concern")
            elif short_tenures > 1:
                score -= 7

        final_score = round(max(0.0, min(100.0, score)), 2)

        return {
            "score": final_score,
            "detail": detail,
            "warnings": warnings,
            "explanation": (
                f"Career consistency {final_score}/100: "
                f"{len(experience)} positions, "
                f"{gaps_detected} gaps, "
                f"{overlaps} overlaps"
            ),
        }

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from a date string."""
        if not date_str:
            return None
        date_str = date_str.strip().lower()
        if date_str in ("present", "current", "now"):
            return 2026
        m = re.search(r"(\d{4})", date_str)
        return int(m.group(1)) if m else None

    # ── Phase 9: Cross-Engine Validation ──────────────────

    def _cross_validate(
        self,
        text: str,
        parsed: Dict[str, Any],
        role_level: str,
        *,
        github_total_commits: int,
        github_score: float,
        product_mindset_score: float,
        github_repos: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Cross-validate resume claims against other engine signals."""
        detail: Dict[str, Any] = {}
        warnings: List[str] = []
        penalty = 0.0

        text_lower = text.lower()

        # 1. Senior title claim vs GitHub complexity (-8 max)
        claims_senior = any(
            kw in text_lower for kw in [
                "senior", "lead", "principal", "staff", "architect",
                "director", "head of", "vp of",
            ]
        )
        detail["claims_senior"] = claims_senior

        if claims_senior:
            if github_total_commits < 100 and github_repos:
                penalty += 5
                warnings.append(
                    "Claims senior title but low GitHub commit count"
                )
                detail["senior_commit_mismatch"] = True

            if github_score < 40 and github_score > 0:
                penalty += 3
                warnings.append(
                    "Claims senior title but GitHub authenticity score is low"
                )
                detail["senior_github_mismatch"] = True

        # 2. Product mindset mismatch (-5 max)
        claims_product = any(
            kw in text_lower for kw in [
                "product", "user experience", "customer impact",
                "business impact", "revenue", "growth",
                "product manager", "product owner",
            ]
        )
        detail["claims_product"] = claims_product

        if claims_product and product_mindset_score < 25 and product_mindset_score > 0:
            penalty += 5
            warnings.append(
                "Claims product focus but product mindset score is low"
            )
            detail["product_mindset_mismatch"] = True

        # 3. Role level mismatch (-7 max)
        if role_level == "senior":
            experience_count = len(parsed["experience"])
            if experience_count <= 1:
                penalty += 4
                warnings.append("Senior role but only 1 experience entry")
            if len(parsed["skills"]) < 3:
                penalty += 3
                warnings.append("Senior role but very few skills listed")

        # Cap penalty
        penalty = round(min(20.0, penalty), 2)

        return {
            "penalty": penalty,
            "detail": detail,
            "warnings": warnings,
            "explanation": (
                f"Cross-validation penalty: {penalty}/20 "
                f"({'applied' if penalty > 0 else 'none'})"
            ),
        }

    # ── Phase 10: Final Score Computation ─────────────────

    def _compute_final_score(
        self,
        *,
        parse_score: float,
        structure_score: float,
        skill_authenticity_score: float,
        role_alignment_score: float,
        career_consistency_score: float,
        readability_analysis: Dict[str, Any],
        stuffing_analysis: Dict[str, Any],
    ) -> float:
        """Compute weighted final score (0–100).

        Weights:
          Structure:           0.25
          Parse Quality:       0.10
          Skill Authenticity:  0.25
          Role Alignment:      0.15
          Career Consistency:  0.15
          Readability:         0.10
        Stuffing adjustment: High=-10, Medium=-5, Low=0
        """
        weighted = (
            structure_score * 0.25
            + parse_score * 0.10
            + skill_authenticity_score * 0.25
            + role_alignment_score * 0.15
            + career_consistency_score * 0.15
            + readability_analysis.get("score", 50) * 0.10
        )

        # Keyword stuffing penalty
        risk = stuffing_analysis.get("risk", "Low")
        if risk == "High":
            weighted -= 10
        elif risk == "Medium":
            weighted -= 5

        return round(max(0.0, min(100.0, weighted)), 2)

    # ── Warning collector ─────────────────────────────────

    def _collect_warnings(
        self,
        structure: Dict[str, Any],
        skill: Dict[str, Any],
        stuffing: Dict[str, Any],
        readability: Dict[str, Any],
        career: Dict[str, Any],
        cross_val: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Collect all warnings from sub-analyses for dashboard display."""
        warnings: List[Dict[str, str]] = []

        def _add(source: str, analysis: Dict[str, Any]) -> None:
            for w in analysis.get("warnings", []):
                severity = "HIGH" if any(
                    kw in w.lower()
                    for kw in ["missing", "high", "excessive", "low"]
                ) else "MEDIUM"
                warnings.append({
                    "source": source,
                    "message": w,
                    "severity": severity,
                })

        _add("Structure", structure)
        _add("Skills", skill)
        _add("Keyword Stuffing", stuffing)
        _add("Readability", readability)
        _add("Career Logic", career)
        _add("Cross-Validation", cross_val)

        return warnings

    # ── Failure helper ────────────────────────────────────

    @staticmethod
    def _failed(reason: str) -> Dict[str, Any]:
        """Return a structured failure result."""
        return {
            "normalized_score": 0.0,
            "structure_score": 0.0,
            "parse_score": 0.0,
            "skill_authenticity_score": 0.0,
            "role_alignment_score": 0.0,
            "career_consistency_score": 0.0,
            "keyword_stuffing_risk": "Unknown",
            "recruiter_readability": "Unknown",
            "cross_validation_penalty": 0.0,
            "raw_metrics": {},
            "explanation": {"error": reason},
            "engine_failed": True,
            "failure_reason": reason,
            "rate_limited": False,
        }
