@echo off
REM ============================================================
REM  AI Application Generator - Windows Setup Script
REM  Run once to create the virtual environment and install deps
REM ============================================================

echo [1/5] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create venv. Ensure Python 3.11+ is installed.
    exit /b 1
)

echo [2/5] Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

echo [3/5] Installing application dependencies...
.venv\Scripts\pip.exe install -e ".[dev]"
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    exit /b 1
)

echo [4/5] Setting up base template virtual environment...
cd base-template
python -m venv .venv
.venv\Scripts\pip.exe install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
cd ..

echo [5/5] Creating default .env file...
if not exist ".env" (
    copy .env.example .env > nul
    echo   Created .env from .env.example
) else (
    echo   .env already exists — skipping
)

echo.
echo ============================================================
echo  Setup complete.
echo  Edit .env to configure ports, paths, and log level.
echo  Run start.bat to launch the application.
echo ============================================================
