"""Resume Parser Service — Extracts structured data from uploaded resumes.

Supports PDF, DOCX, and TXT files.
Extracts: skills, projects, experience (company, role, dates).
"""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import logger

# ── Comprehensive tech-skills dictionary ──────────────────
# Organised by category for better matching. All lower-case.
TECH_SKILLS: Dict[str, List[str]] = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "perl", "lua", "haskell", "elixir", "clojure",
        "dart", "objective-c", "shell", "bash", "powershell", "sql",
        "html", "css", "sass", "scss", "less", "graphql", "solidity",
        "assembly", "fortran", "cobol", "f#", "ocaml", "erlang", "zig",
        "julia", "groovy", "vhdl", "verilog",
    ],
    "frameworks": [
        "react", "react.js", "reactjs", "next.js", "nextjs", "next",
        "angular", "angularjs", "vue", "vue.js", "vuejs", "svelte",
        "nuxt", "nuxt.js", "gatsby", "remix",
        "node.js", "nodejs", "node", "express", "express.js", "expressjs",
        "fastapi", "flask", "django", "spring", "spring boot", "springboot",
        "rails", "ruby on rails", "laravel", "symfony",
        "asp.net", ".net", "dotnet", ".net core",
        "flutter", "react native", "ionic", "xamarin", "swiftui",
        "electron", "tauri",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "pandas", "numpy", "scipy", "matplotlib", "opencv",
        "gin", "echo", "fiber", "actix", "rocket",
        "nestjs", "nest.js", "koa", "hapi", "fastify",
        "tailwind", "tailwindcss", "bootstrap", "material-ui", "mui",
        "chakra ui", "ant design", "styled-components",
        "jquery", "backbone.js", "ember.js",
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "mariadb", "sqlite",
        "mongodb", "dynamodb", "cassandra", "couchdb", "couchbase",
        "redis", "memcached", "elasticsearch", "neo4j", "arangodb",
        "firebase", "firestore", "supabase", "cockroachdb",
        "oracle", "sql server", "mssql", "snowflake", "bigquery",
        "clickhouse", "timescaledb", "influxdb",
    ],
    "devops_cloud": [
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "docker", "kubernetes", "k8s", "terraform", "ansible", "puppet",
        "chef", "vagrant", "jenkins", "github actions", "gitlab ci",
        "circleci", "travis ci", "argocd", "helm",
        "nginx", "apache", "caddy", "traefik",
        "linux", "ubuntu", "centos", "debian",
        "prometheus", "grafana", "datadog", "splunk", "elk",
        "cloudflare", "vercel", "netlify", "heroku", "digitalocean",
        "lambda", "ec2", "s3", "rds", "ecs", "eks", "fargate",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "svn",
        "jira", "confluence", "trello", "asana", "notion",
        "figma", "sketch", "adobe xd",
        "postman", "swagger", "openapi",
        "webpack", "vite", "rollup", "esbuild", "parcel", "babel",
        "jest", "mocha", "chai", "cypress", "playwright", "selenium",
        "pytest", "unittest", "rspec",
        "storybook", "chromatic",
        "rabbitmq", "kafka", "celery", "airflow",
        "graphql", "rest", "grpc", "websocket", "soap",
        "oauth", "jwt", "saml", "openid",
        "ci/cd", "tdd", "bdd", "agile", "scrum", "kanban",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision",
        "reinforcement learning", "generative ai", "llm",
        "large language model", "transformer", "bert", "gpt",
        "hugging face", "langchain", "openai", "chatgpt",
        "stable diffusion", "midjourney",
        "data science", "data engineering", "data analysis",
        "feature engineering", "model deployment", "mlops",
    ],
}

# Flatten all skills into a single set for fast lookup
ALL_SKILLS_FLAT: set[str] = set()
for _cat_skills in TECH_SKILLS.values():
    for _s in _cat_skills:
        ALL_SKILLS_FLAT.add(_s.lower())

# Multi-word skills sorted longest first so greedy matching works
_MULTI_WORD_SKILLS = sorted(
    [s for s in ALL_SKILLS_FLAT if " " in s or "." in s],
    key=len,
    reverse=True,
)

# ── Date parsing patterns ─────────────────────────────────
_MONTH_NAMES = (
    "january|february|march|april|may|june|july|august|september|"
    "october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
)

_DATE_RANGE_RE = re.compile(
    rf"(?P<start>(?:{_MONTH_NAMES})\s*\d{{4}})"
    rf"\s*[-–—to]+\s*"
    rf"(?P<end>(?:{_MONTH_NAMES})\s*\d{{4}}|present|current|now)",
    re.IGNORECASE,
)

_YEAR_RANGE_RE = re.compile(
    r"(?P<start>\d{4})\s*[-–—to]+\s*(?P<end>\d{4}|present|current|now)",
    re.IGNORECASE,
)

# Section header patterns
_SECTION_RE = re.compile(
    r"^[#\s]*(?:(?:professional\s+)?experience|work\s+(?:experience|history)|employment(?:\s+history)?)\s*[:\-—]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_PROJECT_SECTION_RE = re.compile(
    r"^[#\s]*(?:(?:personal\s+|academic\s+|key\s+|notable\s+)?projects?|portfolio)\s*[:\-—]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_EDUCATION_SECTION_RE = re.compile(
    r"^[#\s]*(?:education|academic|qualifications?|certifications?|degrees?)\s*[:\-—]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_SKILLS_SECTION_RE = re.compile(
    r"^[#\s]*(?:(?:technical\s+|core\s+|key\s+)?skills?|(?:technical\s+)?(?:proficiency|competencies?|expertise))\s*[:\-—]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_ANY_SECTION_RE = re.compile(
    r"^[#\s]*(?:experience|work|employment|projects?|portfolio|education|"
    r"academic|qualifications?|certifications?|skills?|proficiency|competencies?|"
    r"expertise|interests?|hobbies|references?|languages?|awards?|publications?|"
    r"achievements?|summary|objective|about)\s*[:\-—]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _parse_month_year(text: str) -> Optional[date]:
    """Parse 'Jan 2020' or 'January 2020' or '2020' into a date."""
    text = text.strip().lower()
    if text in ("present", "current", "now"):
        return date.today()
    # Try month + year
    for fmt in ("%B %Y", "%b %Y", "%B%Y", "%b%Y"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.date()
        except ValueError:
            continue
    # Just year
    m = re.match(r"(\d{4})", text)
    if m:
        return date(int(m.group(1)), 1, 1)
    return None


def _extract_section_text(full_text: str, section_re: re.Pattern, all_section_re: re.Pattern) -> str:
    """Extract the text block between a section header and the next section header."""
    match = section_re.search(full_text)
    if not match:
        return ""
    start = match.end()
    # Find the next section header
    next_match = all_section_re.search(full_text, start)
    end = next_match.start() if next_match else len(full_text)
    return full_text[start:end].strip()


class ResumeParser:
    """Parses resume files and extracts structured data."""

    # ── Text extraction ───────────────────────────────────

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract text from a PDF file."""
        import pdfplumber

        text_parts: List[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text from a DOCX file."""
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

    @staticmethod
    def extract_text_from_txt(file_bytes: bytes) -> str:
        """Extract text from a plain text file."""
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                return file_bytes.decode(encoding)
            except (UnicodeDecodeError, ValueError):
                continue
        return file_bytes.decode("utf-8", errors="replace")

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Route to the correct text extractor based on file extension."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "pdf":
            return self.extract_text_from_pdf(file_bytes)
        elif ext in ("docx",):
            return self.extract_text_from_docx(file_bytes)
        elif ext in ("txt", "text"):
            return self.extract_text_from_txt(file_bytes)
        else:
            # Try PDF first, fall back to text
            try:
                return self.extract_text_from_pdf(file_bytes)
            except Exception:
                return self.extract_text_from_txt(file_bytes)

    # ── Skill extraction ──────────────────────────────────

    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract technical skills from the resume text.

        Returns list of {name: str, years: float}.
        Years defaults to 1.0 if not explicitly mentioned.
        """
        text_lower = text.lower()
        found_skills: Dict[str, float] = {}

        # First try to find a dedicated skills section for more accurate matching
        skills_section = _extract_section_text(text, _SKILLS_SECTION_RE, _ANY_SECTION_RE)
        search_text = skills_section.lower() if skills_section else text_lower

        # 1. Match multi-word skills first (greedy, longest first)
        marked_text = search_text
        for skill in _MULTI_WORD_SKILLS:
            # Use word boundary-ish matching
            pattern = re.compile(r"(?<![a-z])" + re.escape(skill) + r"(?![a-z])", re.IGNORECASE)
            if pattern.search(marked_text):
                found_skills[skill] = 1.0
                # Don't remove from text - single-word parts might match other things

        # 2. Match single-word skills
        words_in_text = set(re.findall(r"\b[a-z][a-z0-9+#.]*\b", search_text))
        for skill in ALL_SKILLS_FLAT:
            if " " in skill or "." in skill:
                continue  # Already handled
            if skill in words_in_text:
                if skill not in found_skills:
                    found_skills[skill] = 1.0

        # 3. Try to extract years of experience for each skill
        # Search line-by-line to avoid cross-line contamination
        text_lines = text_lower.split("\n")
        for skill in list(found_skills.keys()):
            for line in text_lines:
                if skill not in line and skill.replace(".", "") not in line:
                    continue
                # Pattern: "5 years of Python" or "Python (3 years)" or "Python - 4+ years"
                patterns = [
                    rf"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience\s+(?:in|with)\s+)?{re.escape(skill)}",
                    rf"{re.escape(skill)}\s*[-–—:]\s*(\d+)\+?\s*(?:years?|yrs?)",
                    rf"{re.escape(skill)}\s*\((\d+)\+?\s*(?:years?|yrs?)?\)",
                ]
                matched_years = False
                for pat in patterns:
                    m = re.search(pat, line)
                    if m:
                        found_skills[skill] = float(m.group(1))
                        matched_years = True
                        break
                if matched_years:
                    break

        # 4. Deduplicate: if both "react" and "react.js" found, keep the more specific one
        deduped: Dict[str, float] = {}
        skill_list = sorted(found_skills.keys(), key=len, reverse=True)
        for s in skill_list:
            # Check if this skill is a substring of an already-added skill
            is_sub = False
            for existing in deduped:
                if s in existing or existing in s:
                    # Keep the one with more years, or the longer name
                    if found_skills[s] > deduped[existing]:
                        deduped[s] = found_skills[s]
                        if existing != s:
                            del deduped[existing]
                            break
                    is_sub = True
                    break
            if not is_sub:
                deduped[s] = found_skills[s]

        # Filter out overly generic single-char skills like "c" and "r" unless strong evidence
        filtered: Dict[str, float] = {}
        for s, y in deduped.items():
            if len(s) == 1 and s in ("c", "r"):
                # Only keep if appears in skills section or has explicit years
                pattern = re.compile(rf"\b{re.escape(s.upper())}\b")
                if skills_section and pattern.search(skills_section):
                    filtered[s] = y
                elif y > 1.0:
                    filtered[s] = y
            else:
                filtered[s] = y

        # Capitalise nicely
        result = []
        for skill_name, years in filtered.items():
            # Capitalise: keep known forms
            display_name = self._capitalise_skill(skill_name)
            result.append({"name": display_name, "years": years})

        # Sort by name for consistency
        result.sort(key=lambda x: x["name"].lower())
        return result

    @staticmethod
    def _capitalise_skill(name: str) -> str:
        """Return a nicely capitalised skill name."""
        # Known capitalisations
        special = {
            "javascript": "JavaScript", "typescript": "TypeScript",
            "python": "Python", "java": "Java", "c++": "C++", "c#": "C#",
            "c": "C", "r": "R", "go": "Go", "golang": "Go",
            "rust": "Rust", "ruby": "Ruby", "php": "PHP", "swift": "Swift",
            "kotlin": "Kotlin", "scala": "Scala", "dart": "Dart",
            "html": "HTML", "css": "CSS", "sass": "Sass", "scss": "SCSS",
            "sql": "SQL", "graphql": "GraphQL", "bash": "Bash",
            "react": "React", "react.js": "React.js", "reactjs": "React.js",
            "next.js": "Next.js", "nextjs": "Next.js", "next": "Next.js",
            "angular": "Angular", "vue": "Vue", "vue.js": "Vue.js",
            "svelte": "Svelte", "nuxt": "Nuxt.js",
            "node.js": "Node.js", "nodejs": "Node.js", "node": "Node.js",
            "express": "Express", "express.js": "Express.js",
            "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
            "spring": "Spring", "spring boot": "Spring Boot",
            "rails": "Rails", "laravel": "Laravel",
            ".net": ".NET", "asp.net": "ASP.NET",
            "flutter": "Flutter", "react native": "React Native",
            "tensorflow": "TensorFlow", "pytorch": "PyTorch",
            "keras": "Keras", "scikit-learn": "Scikit-learn",
            "pandas": "Pandas", "numpy": "NumPy",
            "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
            "aws": "AWS", "azure": "Azure", "gcp": "GCP",
            "terraform": "Terraform", "ansible": "Ansible",
            "jenkins": "Jenkins", "git": "Git", "github": "GitHub",
            "gitlab": "GitLab", "jira": "Jira",
            "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
            "mysql": "MySQL", "mongodb": "MongoDB", "redis": "Redis",
            "elasticsearch": "Elasticsearch", "firebase": "Firebase",
            "nginx": "Nginx", "linux": "Linux",
            "jest": "Jest", "cypress": "Cypress", "selenium": "Selenium",
            "webpack": "Webpack", "vite": "Vite",
            "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
            "bootstrap": "Bootstrap", "material-ui": "Material-UI",
            "rabbitmq": "RabbitMQ", "kafka": "Kafka", "celery": "Celery",
            "oauth": "OAuth", "jwt": "JWT",
            "ci/cd": "CI/CD", "tdd": "TDD", "agile": "Agile",
            "machine learning": "Machine Learning", "deep learning": "Deep Learning",
            "nlp": "NLP", "computer vision": "Computer Vision",
            "openai": "OpenAI", "langchain": "LangChain",
            "figma": "Figma", "postman": "Postman",
            "vercel": "Vercel", "heroku": "Heroku",
            "supabase": "Supabase", "snowflake": "Snowflake",
        }
        return special.get(name.lower(), name.title())

    # ── Experience extraction ─────────────────────────────

    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience entries from the resume text.

        Returns list of {company, role, start_date, end_date}.
        """
        experience_section = _extract_section_text(text, _SECTION_RE, _ANY_SECTION_RE)
        if not experience_section:
            # Try to find experience anywhere using date patterns
            return self._extract_experience_from_dates(text)

        return self._parse_experience_block(experience_section)

    def _parse_experience_block(self, block: str) -> List[Dict[str, Any]]:
        """Parse an experience section block into structured entries."""
        entries: List[Dict[str, Any]] = []
        lines = block.split("\n")

        current_entry: Dict[str, Any] = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_entry.get("company") or current_entry.get("role"):
                    entries.append(current_entry)
                    current_entry = {}
                continue

            # Skip bullet-point lines (descriptions)
            if line.startswith(("•", "-", "·", "*", "–")):
                continue

            # Try to find date ranges in the line
            date_match = _DATE_RANGE_RE.search(line)
            year_match = _YEAR_RANGE_RE.search(line) if not date_match else None

            if date_match or year_match:
                match = date_match or year_match
                start_str = match.group("start")  # type: ignore
                end_str = match.group("end")  # type: ignore

                start_date = _parse_month_year(start_str)
                end_date = _parse_month_year(end_str)

                # Clean the line of dates to get role/company info
                clean_line = line[:match.start()].strip().rstrip("|-–—,")  # type: ignore
                after_date = line[match.end():].strip().lstrip("|-–—,")  # type: ignore

                # Handle pipe-separated lines: "Role | Company | Date"
                combined_text = " | ".join(p for p in [clean_line, after_date] if p)
                parts = [p.strip() for p in combined_text.split("|") if p.strip()]

                if current_entry.get("company") and not current_entry.get("start_date"):
                    # Add dates to current entry
                    current_entry["start_date"] = str(start_date) if start_date else ""
                    current_entry["end_date"] = str(end_date) if end_date else ""
                    if parts and not current_entry.get("role"):
                        current_entry["role"] = parts[0]
                else:
                    # Start a new entry
                    if current_entry.get("company") or current_entry.get("role"):
                        entries.append(current_entry)

                    current_entry = {
                        "company": "",
                        "role": "",
                        "start_date": str(start_date) if start_date else "",
                        "end_date": str(end_date) if end_date else "",
                    }

                    if len(parts) >= 2:
                        current_entry["role"] = parts[0]
                        current_entry["company"] = parts[1]
                    elif len(parts) == 1:
                        current_entry["role"] = parts[0]

            elif not line.startswith(("•", "-", "·", "*", "–")):
                # This could be a company or role name
                # Handle pipe-separated: "Software Engineer | Google"
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2 and not current_entry.get("role"):
                    if current_entry.get("company") or current_entry.get("role"):
                        entries.append(current_entry)
                    current_entry = {
                        "company": parts[1],
                        "role": parts[0],
                        "start_date": "",
                        "end_date": "",
                    }
                elif not current_entry.get("role"):
                    current_entry["role"] = line
                elif not current_entry.get("company"):
                    current_entry["company"] = line

        # Don't forget last entry
        if current_entry.get("company") or current_entry.get("role"):
            entries.append(current_entry)

        # Clean up entries
        cleaned: List[Dict[str, Any]] = []
        for entry in entries:
            company = entry.get("company", "").strip()
            role = entry.get("role", "").strip()
            # Swap if company looks like a role
            if company and not role:
                role = company
                company = ""
            if role or company:
                cleaned.append({
                    "company": company or "Unknown Company",
                    "role": role or "Unknown Role",
                    "start_date": entry.get("start_date", ""),
                    "end_date": entry.get("end_date", ""),
                })

        return cleaned

    def _extract_experience_from_dates(self, text: str) -> List[Dict[str, Any]]:
        """Fallback: extract experience from date ranges found anywhere."""
        entries: List[Dict[str, Any]] = []
        seen_ranges: set = set()

        for pattern in (_DATE_RANGE_RE, _YEAR_RANGE_RE):
            for match in pattern.finditer(text):
                range_key = (match.group("start"), match.group("end"))
                if range_key in seen_ranges:
                    continue
                seen_ranges.add(range_key)

                start_date = _parse_month_year(match.group("start"))
                end_date = _parse_month_year(match.group("end"))

                # Get the line containing this match
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.end())
                if line_end == -1:
                    line_end = len(text)
                context = text[line_start:match.start()].strip()

                if start_date and end_date:
                    entries.append({
                        "company": context or "Unknown Company",
                        "role": "",
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                    })

        return entries

    # ── Project extraction ────────────────────────────────

    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project names from the resume text.

        Returns list of {name: str, tech: str, description: str}.
        """
        project_section = _extract_section_text(text, _PROJECT_SECTION_RE, _ANY_SECTION_RE)
        if not project_section:
            return []

        projects: List[Dict[str, str]] = []
        lines = project_section.split("\n")

        current_project: Dict[str, str] = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_project.get("name"):
                    projects.append(current_project)
                    current_project = {}
                continue

            # Lines starting with bullets are descriptions
            if line.startswith(("•", "-", "·", "*", "–")) and current_project.get("name"):
                desc = line.lstrip("•-·*– ").strip()
                if current_project.get("description"):
                    current_project["description"] += "; " + desc
                else:
                    current_project["description"] = desc
                # Try to extract tech from description
                if not current_project.get("tech"):
                    techs = self._extract_inline_tech(desc)
                    if techs:
                        current_project["tech"] = ", ".join(techs)
            elif not line.startswith(("•", "-", "·", "*", "–")):
                # This is likely a project name/heading
                if current_project.get("name"):
                    projects.append(current_project)

                # Check for tech in parentheses or after |
                name = line
                tech = ""
                # Pattern: "Project Name (React, Node.js)"
                paren_match = re.search(r"\(([^)]+)\)\s*$", line)
                if paren_match:
                    tech = paren_match.group(1).strip()
                    name = line[:paren_match.start()].strip()
                # Pattern: "Project Name | React, Node.js"
                elif "|" in line:
                    parts = line.split("|", 1)
                    name = parts[0].strip()
                    tech = parts[1].strip()

                # Remove trailing date ranges from name
                name = _DATE_RANGE_RE.sub("", name).strip()
                name = _YEAR_RANGE_RE.sub("", name).strip()
                name = name.rstrip("|-–—, ")

                if name:
                    current_project = {"name": name, "tech": tech, "description": ""}

        # Don't forget last project
        if current_project.get("name"):
            projects.append(current_project)

        return projects

    def _extract_inline_tech(self, text: str) -> List[str]:
        """Extract tech keywords from inline text."""
        found = []
        text_lower = text.lower()
        for skill in _MULTI_WORD_SKILLS:
            if skill in text_lower:
                found.append(self._capitalise_skill(skill))
        words = set(re.findall(r"\b[a-z][a-z0-9+#.]*\b", text_lower))
        for skill in ALL_SKILLS_FLAT:
            if " " in skill:
                continue
            if skill in words and self._capitalise_skill(skill) not in found:
                found.append(self._capitalise_skill(skill))
        return found[:5]  # Limit to top 5

    # ── Main parse method ─────────────────────────────────

    def parse(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parse a resume file and return structured data.

        Returns:
            {
                "raw_text": str,           # Full extracted text
                "skills": [...],           # List of {name, years}
                "experience": [...],       # List of {company, role, start_date, end_date}
                "projects": [...],         # List of {name, tech, description}
            }
        """
        logger.info(f"Parsing resume: {filename} ({len(file_bytes)} bytes)")

        raw_text = self.extract_text(file_bytes, filename)
        if not raw_text.strip():
            logger.warning(f"No text extracted from {filename}")
            return {
                "raw_text": "",
                "skills": [],
                "experience": [],
                "projects": [],
            }

        logger.info(f"Extracted {len(raw_text)} chars from {filename}")

        skills = self.extract_skills(raw_text)
        experience = self.extract_experience(raw_text)
        projects = self.extract_projects(raw_text)

        logger.info(
            f"Parsed resume: {len(skills)} skills, "
            f"{len(experience)} experiences, {len(projects)} projects"
        )

        return {
            "raw_text": raw_text,
            "skills": skills,
            "experience": experience,
            "projects": projects,
        }
