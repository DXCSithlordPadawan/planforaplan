#!/usr/bin/env bash
# ============================================================
#  AI Application Generator - Linux/macOS Setup Script
#  Run once to create the virtual environment and install deps
# ============================================================
set -euo pipefail

echo "[1/5] Creating virtual environment..."
python3 -m venv .venv

echo "[2/5] Upgrading pip..."
.venv/bin/pip install --upgrade pip

echo "[3/5] Installing application dependencies..."
.venv/bin/pip install -e ".[dev]"

echo "[4/5] Setting up base template virtual environment..."
cd base-template
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
cd ..

echo "[5/5] Creating default .env file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
else
    echo "  .env already exists — skipping"
fi

echo ""
echo "============================================================"
echo " Setup complete."
echo " Edit .env to configure ports, paths, and log level."
echo " Run ./start.sh to launch the application."
echo "============================================================"
