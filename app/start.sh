#!/usr/bin/env bash
# ============================================================
#  AI Application Generator - Linux/macOS Start Script
# ============================================================
set -euo pipefail

if [ ! -f ".venv/bin/uvicorn" ]; then
    echo "ERROR: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "WARNING: .env not found. Using defaults from .env.example"
    cp .env.example .env
fi

# Read APP_HOST and APP_PORT from .env (fall back to safe defaults)
APP_HOST=$(grep -E "^APP_HOST=" .env 2>/dev/null | cut -d= -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || true)
APP_PORT=$(grep -E "^APP_PORT=" .env 2>/dev/null | cut -d= -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || true)
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-8000}"

echo "Starting AI Application Generator on http://${APP_HOST}:${APP_PORT}"
echo "Press Ctrl+C to stop."
echo ""

# --reload is intentionally omitted: uvicorn reload wipes in-memory provider state.
# To enable hot-reload during development, add --reload to the line below.
.venv/bin/uvicorn app.main:app --host "${APP_HOST}" --port "${APP_PORT}"
