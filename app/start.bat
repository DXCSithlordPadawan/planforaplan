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

REM Read APP_HOST and APP_PORT from .env (fall back to safe defaults)
set APP_HOST=127.0.0.1
set APP_PORT=8000
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if not "%%a"=="" (
        if "%%a"=="APP_HOST" set APP_HOST=%%b
        if "%%a"=="APP_PORT" set APP_PORT=%%b
    )
)

echo Starting AI Application Generator on http://%APP_HOST%:%APP_PORT%
echo Press Ctrl+C to stop.
echo.

REM --reload is intentionally omitted: uvicorn reload wipes in-memory provider state.
REM To enable hot-reload during development, add --reload to the line below.
.venv\Scripts\uvicorn.exe app.main:app --host %APP_HOST% --port %APP_PORT%
