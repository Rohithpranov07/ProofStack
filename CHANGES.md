# CHANGES.md — Phase 13: Antigravity Fix

**Date**: 2025-01-27  
**Scope**: 9 fix categories, ~30 individual changes  
**Result**: 106/106 tests passing, hackathon-ready grade

---

## Fix 1 — Critical Integrity Fixes

### 1.1 Landing Page Truthfulness (`proofstack-frontend/src/app/page.tsx`)

- **Removed** all false marketing claims ("AI-Powered", "50,000+ Developers", "Enterprise-Grade")
- **Replaced** badge with "10-Engine Algorithmic Verification"
- **Updated** headline to "Résumés describe intent. GitHub proves reality."
- **Replaced** fake feature descriptions with real algorithms: Shannon entropy, z-score burst detection, behavioral pattern analysis
- **Replaced** fake stats (50k+ Developers, 99.7% Accuracy, 10M+ Data Points, 500+ Companies) with real numbers (10 Analysis Engines, 14 Red Flag Types, 3 Role-Weighted Profiles, 100% Deterministic Scoring)
- **Replaced** fake company logos with real API platform logos (GitHub, LeetCode, LinkedIn, StackOverflow)
- **Added** "How It Works" section: 5×2 engine grid showing all 10 engines with descriptions

### 1.2 Chart Data Honesty (`app/api/dashboard.py`, `app/services/github_auth_engine.py`)

- **Added** `_aggregate_monthly_commits()` to GitHub Auth Engine — buckets commit dates into YYYY-MM format using `defaultdict(int)`
- **Added** `monthly_commits` and `repo_details` to engine `raw_metrics` output
- **Rewrote** `_build_commit_timeline` in dashboard.py:
  - Priority 1: Real monthly_commits from engine
  - Priority 2: Per-repo commit counts (deterministic distribution)
  - Priority 3: Honest estimated distribution (position-based weighting, NO `random.seed`)
  - Every data point now has `"source"` field: `"real"`, `"per_repo"`, or `"estimated"`
- **Removed** `import random` — zero randomness in chart synthesis

---

## Fix 2 — Security Fixes

### 2.1 API Authentication (`app/core/auth.py`, `app/main.py`)

- **Created** `app/core/auth.py` — `require_api_key` dependency using `X-API-Key` header
- Uses `secrets.compare_digest` for timing-safe comparison
- Returns 401 (missing key) or 403 (invalid key)
- **All 12 routers** now mounted with `dependencies=[Depends(require_api_key)]`
- Public exceptions: shared dashboard endpoint, demo endpoints, health check

### 2.2 Input Validation (`app/schemas/full_analysis.py`)

- **Added** regex validators for GitHub username (`^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$`) and LeetCode username (`^[a-zA-Z0-9][a-zA-Z0-9_-]{0,98}[a-zA-Z0-9]$`)
- Patterns defined at **module level** (not class level) to avoid Pydantic v2 `ModelPrivateAttr` bug

### 2.3 CORS Hardening (`app/main.py`, `app/core/config.py`)

- **CORS origin** now reads from `settings.FRONTEND_URL` env var instead of hardcoded `*`
- Default: `http://localhost:3000`

### 2.4 Public Router Split (`app/api/dashboard.py`, `app/main.py`)

- **Created** `public_router` in dashboard.py for unauthenticated shared endpoints
- Shared dashboard (`/api/dashboard/shared/{share_token}`) no longer requires API key

### 2.5 Frontend Auth Headers

- **Updated** `proofstack-frontend/src/lib/api.ts` — axios client sends `X-API-Key` header
- **Updated** 3 page files (`analysis/[jobId]/page.tsx`, `analyze/skills/page.tsx`, `analyze/review/page.tsx`) — all `fetch()` calls include `X-API-Key`

---

## Fix 3 — Performance & Scalability

### 3.1 Celery Concurrency (`app/core/celery_app.py`)

- **Added** `worker_concurrency=4` and `result_expires=3600`
- Broker/backend URL now reads from `REDIS_URL` env var

### 3.2 Redis Analysis Cache (`app/utils/cache.py`)

- **Created** `AnalysisCache` class with `get()`, `set()`, `invalidate()`, `close()`
- Key format: `proofstack:analysis:{username}:{role_level}`
- TTL: 1 hour, graceful fallback on Redis errors

### 3.3 Enhanced Health Check (`app/main.py`)

- `/health` endpoint now checks: database connectivity, Redis connectivity, GitHub token rate limit
- Returns per-check status with details

---

## Fix 4 — Test Coverage

### 4.1 GitHub Engine Tests (`tests/test_github_engine.py`) — 22 tests

- Scoring formula verification (7 tests)
- Shannon entropy calculation (4 tests)
- Burst detection with z-scores (5 tests)
- Monthly commit aggregation (3 tests)
- Full analyze flow with mocks (3 tests)

### 4.2 Red Flag Engine Tests (`tests/test_redflag_engine.py`) — 20 tests

- Individual flag detection for all 14 flag types (11 tests)
- Advanced flags: entropy, burst, variance (3 tests)
- Risk level thresholds: HIGH/MODERATE/LOW/MINIMAL (4 tests)
- Missing data graceful handling (3 tests)

### 4.3 Profile Consistency Engine Tests (`tests/test_profile_engine.py`) — 15 tests

- Skill mapping including framework→language (6 tests)
- Scoring formula verification (3 tests)
- Full analyze flow with mocks (5 tests)
- Multi-contributor collaboration signal (1 test)

### 4.4 API Integration Tests (`tests/test_api_integration.py`) — 12 tests

- Health check without auth (2 tests)
- API key auth enforcement (4 tests)
- Protected endpoint verification (3 parametrized tests)
- Input validation rejection (4 tests)
- Schema validation (2 tests)

**Total: 106 tests, all passing**

---

## Fix 5 — Feature Additions

### 5.1 Narrative Engine (`app/services/narrative_engine.py`) — Engine 10

- **6 archetypes**: PROVEN_BUILDER, ACADEMIC_MIND, RISING_TALENT, SPECIALIST, INCONSISTENT, INSUFFICIENT
- Deterministic archetype selection based on engine scores
- Returns: headline, 3-paragraph summary, strengths[], concerns[], recommendation
- **No LLM dependency** — pure template interpolation

### 5.2 Demo Profiles (`app/api/demo.py`)

- **3 pre-loaded profiles**: `strong-fullstack` (PST 87.4), `academic-solver` (PST 62.1), `red-flag-candidate` (PST 31.8)
- Full dashboard-ready JSON including all engines, metrics, narrative
- Public endpoints — no auth required for live demos
- `GET /api/demo/profiles` — list available profiles
- `GET /api/demo/profiles/{profile_id}` — get full demo data

---

## Fix 6 — Database & Migrations

### 6.1 Migration Script (`migrations/add_analysis_version_to_engines.sql`)

- Pre-existing from prior phase

---

## Fix 7 — Docker & Deployment

### 7.1 Backend Dockerfile (`Dockerfile.backend`)

- Python 3.12-slim base, non-root user (`appuser`)
- Health check: `curl --fail http://localhost:8000/health`
- Copies only requirements first for layer caching

### 7.2 Frontend Dockerfile (`Dockerfile.frontend`)

- Node 20-alpine multi-stage build
- Stage 1: dependency install + build with `output: 'standalone'`
- Stage 2: minimal runtime image

### 7.3 Docker Compose (`docker-compose.yml`)

- **5 services**: postgres:16, redis:7-alpine, backend, worker (Celery), frontend
- Health checks on postgres and redis
- Named volume for postgres data persistence
- Environment variables wired from `.env`

### 7.4 Local Dev Script (`start.sh`)

- Checks prerequisites (Python, Node, Redis, PostgreSQL)
- Starts Celery worker, uvicorn backend, Next.js frontend
- Trap-based cleanup on exit

---

## Fix 8 — Frontend Polish

### 8.1 Analysis Step Descriptions (`proofstack-frontend/src/app/analysis/[jobId]/page.tsx`)

- Step descriptions updated with real engine names:
  - "Analyzing GitHub authenticity patterns..."
  - "Running LeetCode problem-solving analysis..."
  - "Checking profile consistency across platforms..."
  - "Scanning for red flags and anomalies..."
  - "Calculating ProofStack Trust score..."

---

## Fix 9 — Monitoring & Observability

### 9.1 Metrics Endpoint (`app/main.py`)

- `GET /metrics` — returns job counts by status and engine inventory
- Queries database for job distribution (pending/running/completed/failed)

### 9.2 Enhanced Health (`app/main.py`)

- Already covered in Fix 3.3

---

## Environment Configuration

### `.env.example` — expanded with:

```
API_KEY=proofstack-demo-2025
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=http://localhost:3000
```

---

## Files Created (12)

| File                               | Purpose                             |
| ---------------------------------- | ----------------------------------- |
| `app/core/auth.py`                 | API key authentication dependency   |
| `app/utils/__init__.py`            | Package init                        |
| `app/utils/cache.py`               | Redis-backed analysis cache         |
| `app/services/narrative_engine.py` | Engine 10 — deterministic summaries |
| `app/api/demo.py`                  | Pre-loaded demo profiles            |
| `tests/test_github_engine.py`      | 22 tests                            |
| `tests/test_redflag_engine.py`     | 20 tests                            |
| `tests/test_profile_engine.py`     | 15 tests                            |
| `tests/test_api_integration.py`    | 12 tests                            |
| `Dockerfile.backend`               | Backend container                   |
| `Dockerfile.frontend`              | Frontend container                  |
| `docker-compose.yml`               | Full stack orchestration            |
| `start.sh`                         | Local dev startup script            |

## Files Modified (14)

| File                                                    | Changes                                  |
| ------------------------------------------------------- | ---------------------------------------- |
| `app/main.py`                                           | Auth, CORS, demo router, health, metrics |
| `app/core/config.py`                                    | API_KEY, REDIS_URL, FRONTEND_URL         |
| `app/core/celery_app.py`                                | REDIS_URL, concurrency, expiry           |
| `app/schemas/full_analysis.py`                          | Regex validators                         |
| `app/api/dashboard.py`                                  | Real chart data, public router           |
| `app/services/github_auth_engine.py`                    | Monthly commit aggregation               |
| `proofstack-frontend/src/app/page.tsx`                  | Complete truthfulness overhaul           |
| `proofstack-frontend/src/lib/api.ts`                    | API key header                           |
| `proofstack-frontend/src/app/analysis/[jobId]/page.tsx` | Auth + step descriptions                 |
| `proofstack-frontend/src/app/analyze/skills/page.tsx`   | Auth header                              |
| `proofstack-frontend/src/app/analyze/review/page.tsx`   | Auth header                              |
| `.env.example`                                          | New env vars                             |
| `tests/test_scoring_integrity.py`                       | Pre-existing                             |
| `CHANGES.md`                                            | This file                                |

---

## Audit Score Impact (estimated)

| Metric           | Before              | After                       |
| ---------------- | ------------------- | --------------------------- |
| API Auth         | None                | API key + timing-safe       |
| Test Coverage    | 37 tests (1 engine) | 106 tests (4 engines + API) |
| False Claims     | 12+ on landing page | 0                           |
| Random in Charts | `random.seed`       | Deterministic real data     |
| Docker Ready     | No                  | Full compose stack          |
| Demo Ready       | No                  | 3 pre-loaded profiles       |
| Engines          | 9                   | 10 (+ Narrative Engine)     |
| Input Validation | None                | Regex on usernames          |
| Health Check     | Basic               | DB + Redis + GitHub         |
