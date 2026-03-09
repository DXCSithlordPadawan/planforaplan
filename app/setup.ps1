#Requires -Version 5.1
# ============================================================
#  AI Application Generator - Windows PowerShell Setup Script
#  Run once to create the virtual environment and install deps
# ============================================================
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "[1/5] Creating virtual environment..."
python -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Failed to create venv. Ensure Python 3.11+ is installed."
    exit 1
}

Write-Host "[2/5] Upgrading pip..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "[3/5] Installing application dependencies..."
& .\.venv\Scripts\pip.exe install -e ".[dev]"
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Dependency installation failed."
    exit 1
}

Write-Host "[4/5] Setting up base template virtual environment..."
Push-Location base-template
python -m venv .venv
& .\.venv\Scripts\pip.exe install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt
Pop-Location

Write-Host "[5/5] Creating default .env file..."
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env from .env.example"
} else {
    Write-Host "  .env already exists - skipping"
}

Write-Host ""
Write-Host "============================================================"
Write-Host " Setup complete."
Write-Host " Edit .env to configure ports, paths, and log level."
Write-Host " Run .\start.ps1 to launch the application."
Write-Host "============================================================"
