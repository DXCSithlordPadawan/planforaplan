#Requires -Version 5.1
# ============================================================
#  AI Application Generator - Run Tests (Windows PowerShell)
# ============================================================
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\pytest.exe")) {
    Write-Error "ERROR: Dev dependencies not installed. Run .\setup.ps1 first."
    exit 1
}

Write-Host "Running tests..."
& .\.venv\Scripts\pytest.exe tests\ -v --tb=short

Write-Host ""
Write-Host "Running security scan (bandit)..."
& .\.venv\Scripts\bandit.exe -r src\ -ll

Write-Host ""
Write-Host "Running dependency audit (pip-audit)..."
& .\.venv\Scripts\pip-audit.exe
