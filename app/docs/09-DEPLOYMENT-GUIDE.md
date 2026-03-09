# AI Application Generator — Deployment Guide

**Version:** 2.1  
**Date:** March 2026  
**Audience:** DevOps, System Administrators  
**Platform:** Windows · Linux · macOS · Container (Podman/Docker)

---

## Table of Contents

1. [Deployment Overview](#1-deployment-overview)
2. [Prerequisites](#2-prerequisites)
3. [Directory Structure](#3-directory-structure)
4. [Installation — Windows](#4-installation--windows)
5. [Installation — Linux / macOS](#5-installation--linux--macos)
6. [Environment Configuration](#6-environment-configuration)
7. [Running in Development Mode](#7-running-in-development-mode)
8. [Running in Production Mode](#8-running-in-production-mode)
9. [Verifying the Deployment](#9-verifying-the-deployment)
10. [Updating an Existing Deployment](#10-updating-an-existing-deployment)
11. [Reverse Proxy Configuration (Network Access)](#11-reverse-proxy-configuration-network-access)
12. [Troubleshooting Deployments](#12-troubleshooting-deployments)

---

## 1. Deployment Overview

The AI Application Generator is a locally-hosted Python FastAPI application. It is designed for single-machine, single-user use. The orchestrator binds to `127.0.0.1:8000` by default, making it accessible only from the local machine.

```mermaid
flowchart TD
    subgraph Machine["Deployment Machine"]
        PY[Python 3.11+]
        VENV[.venv/\nOrchestrator virtualenv]
        BVENV[base-template/.venv/\nGenerated app virtualenv]
        APP[FastAPI Orchestrator\n:8000]
        GEN[Generated App\n:8001]
        DIR[generated-apps/latest/]
    end

    PY --> VENV
    PY --> BVENV
    VENV --> APP
    BVENV --> GEN
    APP -->|writes| DIR
    DIR --> GEN

    BROWSER[User Browser] <-->|:8000| APP
    BROWSER <-->|:8001| GEN
```

Two virtual environments are required:
1. **`.venv/`** — the orchestrator's dependencies (FastAPI, anthropic SDK, psutil, etc.)
2. **`base-template/.venv/`** — pre-installed dependencies for generated apps (FastAPI, jinja2, uvicorn)

---

## 2. Prerequisites

| Requirement | Minimum Version | How to Verify |
|-------------|----------------|---------------|
| Python | 3.11.0 | `python --version` |
| pip | 23.0 | `pip --version` |
| Internet access | — | Required for AI API calls and Tailwind CDN in generated apps |
| Disk space | 500 MB free | For two venvs and generated app deployments |
| RAM | 512 MB free | FastAPI is lightweight; AI API calls are network-bound |
| Ports 8000 and 8001 | Available | `netstat -ano \| findstr ":8000 :8001"` |

**Windows specific:**
- Windows 10 / Windows Server 2019 or later recommended
- PowerShell 5.1 or later (for diagnostic commands)

---

## 3. Directory Structure

After successful installation, the directory structure is:

```
app/
├── .env                        ← Created from .env.example by setup script
├── .env.example                ← Template for environment variables
├── .gitignore
├── .venv/                      ← Orchestrator virtualenv (created by setup script)
│   ├── Scripts/                ← Windows
│   │   ├── uvicorn.exe
│   │   ├── pytest.exe
│   │   └── ...
│   └── bin/                    ← Linux / macOS
│       ├── uvicorn
│       ├── pytest
│       └── ...
├── Containerfile               ← OCI container build file (Podman / Docker)
├── pyproject.toml              ← Project metadata and dependencies
├── setup.bat                   ← One-time setup script (Windows)
├── setup.sh                    ← One-time setup script (Linux/macOS)
├── start.bat                   ← Start the orchestrator (Windows)
├── start.sh                    ← Start the orchestrator (Linux/macOS)
├── test.bat                    ← Run tests and security scans (Windows)
├── test.sh                     ← Run tests and security scans (Linux/macOS)
├── base-template/              ← Pre-installed generated app template
│   ├── .venv/                  ← Generated app virtualenv
│   ├── main.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── generated-apps/             ← Deployment output (created at runtime)
│   └── latest/                 ← Most recent generated app
├── src/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── state.py
│       ├── prompts.py
│       ├── models/
│       ├── routes/
│       ├── services/
│       ├── templates/
│       └── static/
├── tests/
└── docs/
```

---

## 4. Installation — Windows

### Step 1 — Install Python 3.11+

Download from [python.org](https://python.org/downloads). During installation, check:
- ✅ Add Python to PATH
- ✅ Install pip

Verify:
```cmd
python --version
pip --version
```

### Step 2 — Copy Application Files

Place the application directory at `C:\saabdemo\app\` (or any path without spaces).

### Step 3 — Run Setup

```cmd
cd C:\path\to\app
setup.bat
```

`setup.bat` performs five steps:
1. Creates `.venv\` using the system Python
2. Upgrades pip inside `.venv\`
3. Installs all dependencies from `pyproject.toml` (including dev tools)
4. Creates `base-template\.venv\` and installs `base-template\requirements.txt`
5. Creates `.env` from `.env.example` if `.env` does not already exist

Expected output ends with:
```
============================================================
 Setup complete.
 Edit .env to configure ports, paths, and log level.
 Run start.bat to launch the application.
============================================================
```

If any step shows an error, see Section 12 (Troubleshooting).

### Step 4 — Review the Environment File

`setup.bat` creates `.env` automatically from `.env.example`. Review and edit it if needed:

```cmd
notepad .env
```

The defaults work for a standard local deployment. Edit `.env` only if you need to change ports, paths, or log level.

### Step 5 — Start the Application

```cmd
start.bat
```

Expected output:
```
Starting AI Application Generator on http://127.0.0.1:8000
Press Ctrl+C to stop.

INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 6 — Verify

Open a browser and navigate to `http://127.0.0.1:8000`. The AI Application Generator interface should load.

Run a health check:
```cmd
curl http://127.0.0.1:8000/api/health
```
Expected: `{"status":"ok"}`

---

## 5. Installation — Linux / macOS

Shell scripts matching the Windows `.bat` files are provided for Linux and macOS.

### Step 1 — Install Python 3.11+

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv
python3 --version
```

**macOS (Homebrew):**
```bash
brew install python@3.12
python3 --version
```

### Step 2 — Copy Application Files

Place the application directory at a path of your choice (e.g. `~/app`).

### Step 3 — Run Setup

```bash
cd /path/to/app
chmod +x setup.sh start.sh test.sh
./setup.sh
```

`setup.sh` performs the same five steps as `setup.bat`:
1. Creates `.venv/` using the system `python3`
2. Upgrades pip inside `.venv/`
3. Installs all dependencies from `pyproject.toml` (including dev tools)
4. Creates `base-template/.venv/` and installs `base-template/requirements.txt`
5. Creates `.env` from `.env.example` if `.env` does not already exist

### Step 4 — Review the Environment File

```bash
nano .env   # or any editor
```

### Step 5 — Start the Application

```bash
./start.sh
```

### Step 6 — Verify

```bash
curl http://127.0.0.1:8000/api/health
```
Expected: `{"status":"ok"}`

On Linux/macOS, the generated app's uvicorn executable will be at `base-template/.venv/bin/uvicorn`. The `_uvicorn_executable()` function in `process_service.py` handles the platform difference automatically.

---

## 6. Environment Configuration

Edit `.env` in the application directory to configure the deployment:

```env
# Orchestrator bind settings
APP_HOST=127.0.0.1
APP_PORT=8000

# Deployment paths (relative to working directory when the server starts)
DEPLOY_DIR=generated-apps/latest
BASE_TEMPLATE_DIR=base-template

# Port for generated applications
GENERATED_APP_PORT=8001

# Logging level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

### Configuration Notes

**`APP_HOST`** — Set to `127.0.0.1` for local-only access. Change to `0.0.0.0` only if a network-accessible deployment is needed (and only with authentication and HTTPS in place — see Section 11).

**`DEPLOY_DIR`** and **`BASE_TEMPLATE_DIR`** — These are resolved relative to the working directory when the server starts. Use absolute paths if starting the server from a different directory.

> **Windows:** Use forward slashes `/` or doubled backslashes `\\` in paths — Python's `pathlib` handles both.
>
> **Linux/macOS:** Use standard Unix paths.

```env
# Windows absolute path example
DEPLOY_DIR=C:/path/to/app/generated-apps/latest
BASE_TEMPLATE_DIR=C:/path/to/app/base-template

# Linux/macOS absolute path example
DEPLOY_DIR=/home/user/app/generated-apps/latest
BASE_TEMPLATE_DIR=/home/user/app/base-template
```

**`LOG_LEVEL`** — Use `DEBUG` only for troubleshooting. Debug logging is verbose and may capture request details.

---

## 7. Running in Development Mode

Development mode enables auto-reload on code changes.

**Windows:**
```cmd
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Linux / macOS:**
```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

This is equivalent to what `start.bat` / `start.sh` runs. Changes to `src/app/` files will restart the server automatically.

**Note:** Auto-reload does not restart the generated app subprocess or affect in-memory state (which is reset on server restart).

---

## 8. Running in Production Mode

For a stable production deployment (no auto-reload):

**Windows:**
```cmd
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Linux / macOS:**
```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Single worker only:** The application uses module-level in-memory state (`state.py`). Multiple workers would not share state and would cause inconsistent behaviour. Always use `--workers 1`.

**Starting automatically on system boot (Windows Service):**

Use NSSM (Non-Sucking Service Manager) or Windows Task Scheduler to start `start.bat` at login:

```cmd
REM Using Task Scheduler (run as administrator) — adjust the path to your app directory
schtasks /create /tn "AI App Generator" /tr "C:\path\to\app\start.bat" /sc onlogon /ru SYSTEM
```

For a proper Windows Service installation, NSSM is recommended:
```cmd
nssm install AIAppGenerator "C:\path\to\app\.venv\Scripts\uvicorn.exe"
nssm set AIAppGenerator AppParameters "app.main:app --host 127.0.0.1 --port 8000"
nssm set AIAppGenerator AppDirectory "C:\path\to\app"
nssm start AIAppGenerator
```

---

## 9. Verifying the Deployment

Run this verification sequence after any deployment:

**Windows:**
```cmd
REM 1. Health endpoint
curl http://127.0.0.1:8000/api/health
REM Expected: {"status":"ok"}

REM 2. Status endpoint
curl http://127.0.0.1:8000/api/status
REM Expected: {"phase":"idle","progress":0,"message":"Ready","url":null}

REM 3. Security headers present
curl -I http://127.0.0.1:8000/ | findstr "X-Frame-Options X-Content-Type Content-Security"
```

**Linux / macOS:**
```bash
# 1. Health endpoint
curl http://127.0.0.1:8000/api/health
# Expected: {"status":"ok"}

# 2. Status endpoint
curl http://127.0.0.1:8000/api/status

# 3. Security headers present
curl -sI http://127.0.0.1:8000/ | grep -i "x-frame-options\|x-content-type\|content-security"
```

---

## 10. Updating an Existing Deployment

### Minor Update (code changes only, no dependency changes)

1. Stop the server (Ctrl+C).
2. Replace the modified files in `src/app/`.
3. Start the server with `start.bat` (Windows) or `./start.sh` (Linux/macOS).

### Dependency Update

1. Stop the server.
2. Edit `pyproject.toml` with new version constraints.
3. Reinstall:

   **Windows:**
   ```cmd
   .venv\Scripts\pip.exe install -e ".[dev]"
   ```
   **Linux / macOS:**
   ```bash
   .venv/bin/pip install -e ".[dev]"
   ```
4. Rebuild base template venv (see Maintenance Guide Section 5).
5. Run `test.bat` / `./test.sh` — all tests must pass.
6. Start the server.

### Full Reinstall

**Windows:**
```cmd
REM Stop the server first
rmdir /s /q .venv
rmdir /s /q base-template\.venv
setup.bat
```

**Linux / macOS:**
```bash
rm -rf .venv base-template/.venv
./setup.sh
```

---

## 11. Reverse Proxy Configuration (Network Access)

> ⚠️ **Security Warning:** Making this application accessible over a network without authentication is a security risk. Only proceed after implementing bearer token authentication and enabling HTTPS.

If the application must be accessed from another machine on the network, configure a reverse proxy (nginx or Caddy) with HTTPS.

### nginx Example Configuration

```nginx
server {
    listen 443 ssl;
    server_name your-hostname.local;

    ssl_certificate     /etc/ssl/certs/app.crt;
    ssl_certificate_key /etc/ssl/private/app.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Proxy to FastAPI orchestrator
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
```

### Required Additional Changes for Network Deployment

1. In `main.py`, update CORS to include the proxy hostname.
2. Add bearer token authentication middleware.
3. Change `APP_HOST` to `127.0.0.1` (proxy handles external access).
4. Remove `'unsafe-inline'` from CSP by externalising the JavaScript.
5. Add rate limiting with `slowapi`.

---

## 12. Troubleshooting Deployments

### `setup.bat` / `setup.sh` fails at dependency install step

- Check internet connectivity.
- Check if a corporate proxy is blocking pip: set `HTTP_PROXY` and `HTTPS_PROXY` environment variables.
- Manually upgrade pip and retry:

  **Windows:** `.venv\Scripts\pip.exe install --upgrade pip`  
  **Linux/macOS:** `.venv/bin/pip install --upgrade pip`

### `ModuleNotFoundError: No module named 'app'`

The server cannot find the `src/app` package. Ensure you are running the start script from the app directory and that the package is installed:

**Windows:**
```cmd
cd C:\path\to\app
.venv\Scripts\pip.exe install -e .
start.bat
```

**Linux / macOS:**
```bash
cd /path/to/app
.venv/bin/pip install -e .
./start.sh
```

### Server starts but `.env` not found

Run `setup.bat` or `setup.sh` — it creates `.env` automatically. Or create it manually:

**Windows:** `copy .env.example .env`  
**Linux/macOS:** `cp .env.example .env`

### Port 8000 is already in use

Change `APP_PORT` in `.env` to an unused port (e.g., 8080).

### Generated apps fail to start with `No module named 'fastapi'`

The `base-template/.venv/` is missing or broken. Rebuild it:

**Windows:**
```cmd
cd base-template
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
cd ..
```

**Linux / macOS:**
```bash
cd base-template
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ..
```

---

*Document maintained at `app/docs/09-DEPLOYMENT-GUIDE.md`*
