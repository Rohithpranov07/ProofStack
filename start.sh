#!/usr/bin/env bash
# ProofStack — Local Development Startup Script
#
# Usage:
#   chmod +x start.sh && ./start.sh
#
# Prerequisites:
#   - PostgreSQL running on localhost:5432
#   - Redis running on localhost:6379
#   - Python 3.12+ with venv
#   - Node.js 20+
#
# This script starts all three services (backend, worker, frontend) in parallel.
# Press Ctrl+C to stop all services.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ProofStack — Local Dev Startup       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Check prerequisites ──────────────────────────────────
check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}✗ $1 not found. Please install it.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $1 found${NC}"
}

echo -e "${YELLOW}Checking prerequisites...${NC}"
check_cmd python3
check_cmd redis-cli
check_cmd node

# Check .env
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found. Copy from .env.example:${NC}"
    echo "  cp .env.example .env"
    exit 1
fi
echo -e "${GREEN}✓ .env found${NC}"

# Check redis
if ! redis-cli ping &> /dev/null; then
    echo -e "${RED}✗ Redis not responding. Start with: brew services start redis${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis responding${NC}"

# ── Activate venv ─────────────────────────────────────────
if [ -d venv ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Python venv activated${NC}"
else
    echo -e "${YELLOW}Creating Python venv...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Python venv created and deps installed${NC}"
fi

# ── Install frontend deps if needed ──────────────────────
if [ ! -d proofstack-frontend/node_modules ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    (cd proofstack-frontend && npm install)
fi
echo -e "${GREEN}✓ Frontend dependencies ready${NC}"

echo ""
echo -e "${BLUE}Starting services...${NC}"
echo ""

# ── Trap Ctrl+C to kill all background processes ─────────
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all services...${NC}"
    kill 0 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── Start services ────────────────────────────────────────
echo -e "${GREEN}[1/3]${NC} Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info --concurrency=4 --pool=prefork &

echo -e "${GREEN}[2/3]${NC} Starting FastAPI backend on :8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

echo -e "${GREEN}[3/3]${NC} Starting Next.js frontend on :3000..."
(cd proofstack-frontend && npm run dev) &

echo ""
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${GREEN}All services running!${NC}"
echo -e "  Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "  Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "  Health:   ${BLUE}http://localhost:8000/health${NC}"
echo -e "  Demo:     ${BLUE}http://localhost:8000/api/demo/profiles${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

wait
