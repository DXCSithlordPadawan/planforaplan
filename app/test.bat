@echo off
REM ============================================================
REM  AI Application Generator - Run Tests (Windows)
REM ============================================================

if not exist ".venv\Scripts\pytest.exe" (
    echo ERROR: Dev dependencies not installed. Run setup.bat first.
    exit /b 1
)

echo Running tests...
.venv\Scripts\pytest.exe tests\ -v --tb=short

echo.
echo Running security scan (bandit)...
.venv\Scripts\bandit.exe -r src\ -ll

echo.
echo Running dependency audit (pip-audit)...
.venv\Scripts\pip-audit.exe
