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

echo "Starting AI Application Generator on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop."
echo ""

.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
