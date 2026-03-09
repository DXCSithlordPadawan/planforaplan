#Requires -Version 5.1
# ============================================================
#  AI Application Generator - Windows PowerShell Start Script
# ============================================================
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\uvicorn.exe")) {
    Write-Error "ERROR: Virtual environment not found. Run .\setup.ps1 first."
    exit 1
}

if (-not (Test-Path ".env")) {
    Write-Warning "WARNING: .env not found. Using defaults from .env.example"
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting AI Application Generator on http://127.0.0.1:8000"
Write-Host "Press Ctrl+C to stop."
Write-Host ""

& .\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
