#Requires -Version 5.1
# ============================================================
#  AI Application Generator - Windows PowerShell Setup Script
#  Run once to create the virtual environment and install deps
# ============================================================
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "[1/5] Creating virtual environment..."
# Resolve Python: prefer py launcher (works even when App Execution Aliases
# block the bare 'python' / 'python3.13' commands on Windows 10/11).
$pythonExe = $null
foreach ($candidate in @("py", "python3.13", "python3", "python")) {
    try {
        $ver = & $candidate --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3\.([0-9]+)" -and [int]$Matches[1] -ge 11) {
            $pythonExe = $candidate
            Write-Host "  Using Python: $ver ($candidate)"
            break
        }
    } catch { }
}
if (-not $pythonExe) {
    Write-Error "ERROR: Python 3.11+ not found. Install from python.org or the Microsoft Store, then disable App Execution Aliases for 'python.exe' in Settings > Apps > Advanced app settings > App execution aliases."
    exit 1
}
& $pythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Failed to create venv."
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

Write-Host "[4/5] Pre-installing base template dependencies..."
# The generated app runs inside the planforaplan host venv (no separate venv
# is created per deployment). Pre-installing the base requirements here means
# the first deployment has everything it needs without a pip call at runtime.
& .\.venv\Scripts\pip.exe install --quiet -r base-template\requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Failed to install base template dependencies."
    exit 1
}
Write-Host "  Base template dependencies installed into host venv."

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
