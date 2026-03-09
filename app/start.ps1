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

# Read APP_HOST and APP_PORT from .env (fall back to safe defaults)
$appHost = "127.0.0.1"
$appPort = "8000"
if (Test-Path ".env") {
    foreach ($line in (Get-Content ".env")) {
        if ($line -match "^APP_HOST=(.+)") { $appHost = $matches[1].Trim() }
        if ($line -match "^APP_PORT=(.+)") { $appPort = $matches[1].Trim() }
    }
}

Write-Host "Starting AI Application Generator on http://${appHost}:${appPort}"
Write-Host "Press Ctrl+C to stop."
Write-Host ""

& .\.venv\Scripts\uvicorn.exe app.main:app --host $appHost --port $appPort --reload
