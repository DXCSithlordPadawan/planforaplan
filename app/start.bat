@echo off
REM ============================================================
REM  AI Application Generator - Windows Start Script
REM ============================================================

if not exist ".venv\Scripts\uvicorn.exe" (
    echo ERROR: Virtual environment not found. Run setup.bat first.
    exit /b 1
)

if not exist ".env" (
    echo WARNING: .env not found. Using defaults from .env.example
    copy .env.example .env > nul
)

echo Starting AI Application Generator on http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.

.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
