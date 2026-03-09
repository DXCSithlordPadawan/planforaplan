#!/usr/bin/env bash
# ============================================================
#  AI Application Generator - Run Tests (Linux/macOS)
# ============================================================
set -euo pipefail

if [ ! -f ".venv/bin/pytest" ]; then
    echo "ERROR: Dev dependencies not installed. Run ./setup.sh first."
    exit 1
fi

echo "Running tests..."
.venv/bin/pytest tests/ -v --tb=short

echo ""
echo "Running security scan (bandit)..."
.venv/bin/bandit -r src/ -ll

echo ""
echo "Running dependency audit (pip-audit)..."
.venv/bin/pip-audit
