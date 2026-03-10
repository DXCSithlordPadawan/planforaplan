# AI Application Generator — Support Tasks Guide

**Version:** 2.0  
**Date:** March 2026  
**Audience:** Support staff, system administrators, L1/L2/L3 engineers

---

## Table of Contents

1. [Support Tiers](#1-support-tiers)
2. [Diagnostic First Steps](#2-diagnostic-first-steps)
3. [L1 — Common User Issues](#3-l1--common-user-issues)
4. [L2 — Application and Server Issues](#4-l2--application-and-server-issues)
5. [L3 — Code-Level Issues](#5-l3--code-level-issues)
6. [Log Locations and Reading Logs](#6-log-locations-and-reading-logs)
7. [Health Check Procedures](#7-health-check-procedures)
8. [Port Conflict Resolution](#8-port-conflict-resolution)
9. [Dependency Verification](#9-dependency-verification)
10. [Resetting to a Clean State](#10-resetting-to-a-clean-state)
11. [Support Escalation Checklist](#11-support-escalation-checklist)

---

## 1. Support Tiers

| Tier | Scope | Who Handles |
|------|-------|-------------|
| L1 | User-facing issues: API key errors, browser not opening, simple configuration questions | Help desk / end-user support |
| L2 | Server and environment issues: ports blocked, dependencies missing, base template broken, startup failures | System administrator / DevOps |
| L3 | Code defects, AI provider integration failures, security incidents, architecture changes | Developer / application owner |

---

## 2. Diagnostic First Steps

Before investigating any issue, collect the following information:

1. **Operating system and version** — `winver` on Windows
2. **Python version** — `.venv\Scripts\python.exe --version`
3. **Application version** — check `pyproject.toml`, field `version`
4. **Which AI provider is in use** — Claude or Minimax
5. **What the user was doing** — which step in the workflow failed
6. **Exact error message** — from the browser UI and/or terminal window
7. **Terminal output** — screenshot or copy of the Command Prompt showing the server log

---

## 3. L1 — Common User Issues

### 3.1 "Provider not configured" message in the browser

**Cause:** The user has not submitted their API key, or the page was reloaded and the in-memory state was cleared.

**Resolution:**
1. Ask the user to re-enter their API key in the configuration panel.
2. Select the correct provider from the dropdown.
3. Click **Validate & Save** and confirm the green tick appears.

---

### 3.2 "Invalid API key" error

**Cause:** The key was typed incorrectly, contains spaces, or has been revoked.

**Resolution:**
1. Ask the user to copy the key directly from their provider console (not from a text editor where it may have been modified).
2. Confirm the selected provider matches the key type (Claude keys start with `sk-ant-`).
3. If the key was revoked, the user must generate a new one from their provider console.

---

### 3.3 Browser does not open automatically after deployment

**Cause:** The `webbrowser.open()` call failed silently (no default browser set, or sandboxed environment).

**Resolution:**
1. Ask the user to navigate manually to `http://127.0.0.1:8001`.
2. Check the terminal for any error message after `"Browser launched"`.
3. Confirm a default browser is set in Windows settings.

---

### 3.4 Generation appears to hang at the same percentage

**Cause:** The AI API call is in progress (this is normal for 30–90 seconds) or the connection was lost.

**Resolution:**
1. Advise the user to wait up to 2 minutes for the AI response.
2. If after 2 minutes there is no progress, ask the user to click **■ Cancel** and retry.
3. If retries fail consistently, escalate to L2 to check network and API connectivity.

---

### 3.5 Generated application shows a blank page or "Internal Server Error"

**Cause:** The AI-generated code has a bug or syntax error.

**Resolution:**
1. Ask the user to go back, edit the plan to be more explicit, and regenerate.
2. Alternatively, advise the user to check `generated-apps\latest\main.py` for obvious errors.
3. If this recurs with the same requirement, escalate to L3 for prompt engineering review.

---

## 4. L2 — Application and Server Issues

### 4.1 `start.bat` fails with "Virtual environment not found"

**Cause:** `setup.bat` was not run, or it failed partway through.

**Resolution:**
```cmd
cd C:\saabdemo\app
setup.bat
```
Watch for error messages. Common failures:
- Python not in PATH → install Python 3.11+ and ensure "Add to PATH" was checked during install
- pip install failure → check internet connectivity; try `pip install --upgrade pip` first

---

### 4.2 Server starts but browser cannot reach `http://127.0.0.1:8000`

**Cause:** Firewall blocking port 8000, or server crashed at startup.

**Resolution:**
1. Check the terminal — look for `"AI Application Generator starting on http://127.0.0.1:8000"`. If absent, the server crashed at startup.
2. Check Windows Firewall or corporate security software is not blocking port 8000.
3. Try accessing `http://localhost:8000/api/health` from the terminal:
   ```cmd
   curl http://127.0.0.1:8000/api/health
   ```
4. If the firewall is blocking, add an inbound rule for TCP port 8000 (local only).

---

### 4.3 Port 8001 is already in use and the generated app will not start

**Cause:** A previous generated application process did not terminate cleanly.

**Resolution — Automatic:** The system will attempt to kill the process on port 8001 automatically via psutil before each generation. If this fails:

**Resolution — Manual:**
```cmd
REM Find the process using port 8001
netstat -ano | findstr :8001

REM Kill it by PID (replace 12345 with actual PID)
taskkill /PID 12345 /F
```

---

### 4.4 Base template `.venv` is broken or missing Python packages

**Cause:** The base template venv was installed with a different Python version, or packages were corrupted.

**Resolution:**
```cmd
cd C:\saabdemo\app\base-template

REM Remove broken venv
rmdir /s /q .venv

REM Recreate
python -m venv .venv
.venv\Scripts\pip.exe install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
```

---

### 4.5 `setup.bat` installed dependencies but `import fastapi` fails

**Cause:** The application is being run outside the virtual environment.

**Resolution:**
1. Confirm `start.bat` is being used (it uses `.venv\Scripts\uvicorn.exe`).
2. Do not run `python src/app/main.py` directly without activating `.venv` first.
3. If using a custom launch approach, activate with `.venv\Scripts\activate.bat` first.

---

### 4.6 Configuration changes in `.env` are not taking effect

**Cause:** The server was not restarted after editing `.env`.

**Resolution:**
1. Stop the server (Ctrl+C in terminal).
2. Edit `.env`.
3. Run `start.bat` again.

---

## 5. L3 — Code-Level Issues

### 5.1 AI response consistently returns no XML file blocks

**Symptom:** WebSocket shows `"No files were extracted from the AI response."` on every attempt.

**Investigation:**
1. Enable DEBUG logging: set `LOG_LEVEL=DEBUG` in `.env` and restart.
2. The full AI response will be logged. Check whether the AI is wrapping files in `<file path="...">` tags.
3. Check `prompts.py` `CODE_SYSTEM_PROMPT` — the XML format instructions must be present and unambiguous.

**Resolution:**
- If the AI model has changed its output format, update `parse_generated_files()` in `file_service.py` to match.
- Consider adding few-shot examples to `CODE_SYSTEM_PROMPT`.

---

### 5.2 `wait_for_ready()` times out on valid applications

**Symptom:** The uvicorn process starts but the readiness signal is never detected.

**Investigation:**
1. Manually run uvicorn from `generated-apps/latest/`:
   ```cmd
   .venv\Scripts\uvicorn.exe main:app --port 8001
   ```
2. Observe the exact startup output. The readiness check looks for `"Application startup complete"` or `"Uvicorn running on"`.
3. If uvicorn outputs a different string (possible in a future uvicorn release), update the `wait_for_ready()` detection strings in `process_service.py`.

---

### 5.3 Security scan (`bandit`) reports a new HIGH finding

**Action required:** Do not deploy to production until resolved.

**Process:**
1. Run `test.bat` and review bandit output.
2. Identify the file and line number.
3. Review the finding. If it is a false positive, add a `# nosec` comment with justification.
4. If it is a real vulnerability, fix the code and re-run `test.bat` to confirm the finding is resolved.
5. Update the Security Analysis document (`07-SECURITY-COMPLIANCE.md`) with the finding and its resolution.

---

### 5.4 Dependency vulnerability found by `pip-audit`

**Action required:** Assess severity before deploying.

**Process:**
1. Run `test.bat` and review pip-audit output.
2. For CRITICAL or HIGH CVEs: update the affected package to the fixed version in `pyproject.toml` and re-run setup.
3. For MEDIUM or LOW CVEs: log the finding in the Security Analysis document and set a review date.
4. If no fix is available, document the mitigating controls and escalate to the application owner.

---

## 6. Log Locations and Reading Logs

### Orchestrator Server Logs

Logs are written to **stdout** in the terminal window running `start.bat`. They are not written to a file by default.

Log format:
```
2026-03-06 14:23:01 app.routes.api INFO Generation/deployment failed: Claude rate limit exceeded.
```

Fields: `timestamp | logger_name | level | message`

Log levels: `DEBUG < INFO < WARNING < ERROR < CRITICAL`

To increase verbosity, set `LOG_LEVEL=DEBUG` in `.env` and restart.

To capture logs to a file (Windows):
```cmd
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 > app.log 2>&1
```

### WebSocket Logs (Browser)

The terminal panel in the Execution view shows `info`, `success`, and `error` messages broadcast during generation. These are the most user-visible logs.

### Generated App Logs

The generated application's stdout is piped into the orchestrator's readiness monitor and shown in the WebSocket terminal panel during deployment. After the app is running, its logs are discarded. To capture them, run the generated app manually:
```cmd
cd generated-apps\latest
.venv\Scripts\uvicorn.exe main:app --port 8001 > genapp.log 2>&1
```

---

## 7. Health Check Procedures

### Quick Health Check

```cmd
curl http://127.0.0.1:8000/api/health
```

Expected response: `{"status": "ok"}`

### Full System Check

```cmd
REM 1. Orchestrator responsive
curl http://127.0.0.1:8000/api/health

REM 2. Status endpoint working
curl http://127.0.0.1:8000/api/status

REM 3. Index page serving HTML
curl http://127.0.0.1:8000/

REM 4. Python and venv functional
.venv\Scripts\python.exe -c "import fastapi; import anthropic; import psutil; print('OK')"

REM 5. Base template venv functional
base-template\.venv\Scripts\python.exe -c "import fastapi; import uvicorn; print('OK')"
```

---

## 8. Port Conflict Resolution

| Port | Service | Action if blocked |
|------|---------|-------------------|
| 8000 | AI Application Generator orchestrator | Change `APP_PORT` in `.env`; update `start.bat` accordingly |
| 8001 | Generated application | Change `GENERATED_APP_PORT` in `.env`; system uses new port automatically |

**Finding what is on a port (Windows):**
```cmd
netstat -ano | findstr :<port>
tasklist | findstr <PID>
```

**Finding what is on a port (PowerShell):**
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object State, OwningProcess
Get-Process -Id <PID>
```

---

## 9. Dependency Verification

Verify all runtime dependencies are installed and importable:

```cmd
.venv\Scripts\python.exe -c "
import fastapi, uvicorn, anthropic, httpx
import jinja2, pydantic, pydantic_settings
import dotenv, psutil, cryptography, multipart
print('All dependencies OK')
"
```

Check installed versions:
```cmd
.venv\Scripts\pip.exe list | findstr -i "fastapi uvicorn anthropic httpx jinja2 pydantic psutil cryptography"
```

Check for outdated packages:
```cmd
.venv\Scripts\pip.exe list --outdated
```

---

## 10. Resetting to a Clean State

### Reset in-memory session state (soft reset)

Stop the server and restart it:
```cmd
Ctrl+C
start.bat
```
This clears the provider, process handle, and WebSocket connections from memory.

### Reset generated apps (remove deployment)

```cmd
rmdir /s /q generated-apps\latest
```
The directory will be recreated on the next generation.

### Full clean reinstall

```cmd
rmdir /s /q .venv
rmdir /s /q base-template\.venv
rmdir /s /q generated-apps
del .env
setup.bat
copy .env.example .env
```

---

## 12. Known Issues and Fixes Log

### Session: 2026-03-10 — Provider Configuration Fixes

The following defects were identified and resolved in `src/app/services/ai_provider.py`, `src/app/routes/api.py`, and the start scripts.

---

#### Issue 1 — OpenRouter / Custom provider returns HTTP 429 on config save

**Symptom:** Configuring a free-tier OpenRouter model (e.g. `cognitivecomputations/dolphin-mistral-24b-venice-edition:free`) produced a 429 Too Many Requests error immediately on clicking *Validate & Save*.

**Root cause:** The `POST /api/config` endpoint was making a live probe call (`provider.generate("Hello", ...)`) to validate the key before storing it. Free-tier OpenRouter models have very low rate limits (1–3 req/min); the probe call consumed the quota immediately.

**Fix:** Removed the probe call from `configure()` in `routes/api.py`. The provider is now stored immediately. An invalid key will surface naturally on the first `POST /api/plan` or `POST /api/generate` call.

**Files changed:** `src/app/routes/api.py`

---

#### Issue 2 — Provider shows as "not configured" after a successful config save

**Symptom:** After a successful *Validate & Save*, clicking *Generate Plan* returned "Provider not configured".

**Root cause:** All three start scripts (`start.ps1`, `start.bat`, `start.sh`) launched uvicorn with the `--reload` flag. Hot-reload restarts the worker process on any file-system change, wiping the module-level `_provider` global in `state.py` back to `None`.

**Fix:** Removed `--reload` from all three start scripts. A comment was added explaining why — reload is incompatible with in-memory session state.

**Files changed:** `start.ps1`, `start.bat`, `start.sh`

---

#### Issue 3 — Minimax returns HTTP 401 "Invalid API key" on Generate Plan

**Symptom:** Minimax provider configured successfully, but `POST /api/plan` returned HTTP 502 with message "Invalid Minimax API key or wrong API endpoint".

**Root cause (first):** `MinimaxProvider.API_URL` was set to the old `api.minimax.chat` domain, which is no longer active. Minimax's current host is `api.minimax.io`. Sending a valid key to the wrong host results in a 401.

**Root cause (second):** After fixing the host, the provider was still hitting `/v1/chat/completions` (OpenAI-compatible path). Keys issued from `platform.minimax.io` are provisioned for the **native** endpoint `/v1/text/chatcompletion_v2`, not the OpenAI-compat layer.

**Root cause (third):** The `generate()` payload always included `{"role": "system", "content": ""}` even when `system_prompt` was empty. Minimax rejects an empty-content system message.

**Fix:** Updated `MinimaxProvider` to use `API_BASE = "https://api.minimax.io"` and `API_PATH = "/v1/text/chatcompletion_v2"`. The system message is now only added to the payload when `system_prompt` is non-empty. Response parsing falls back to the `reply` field if `choices` is absent.

**Files changed:** `src/app/services/ai_provider.py`

---

#### Issue 4 — Minimax error 1004 persists after endpoint fix

**Symptom:** After switching to the native endpoint, HTTP 200 was returned but `base_resp.status_code = 1004` in the body: *"login fail: Please carry the API secret key in the Authorization field"*.

**Root cause:** The API key being submitted was an **OpenRouter key** (`sk-o...`, length 73) pasted into the Minimax provider field by mistake. Minimax's native API requires a key issued from `platform.minimax.io` (JWT format, `eyJ...`, 150+ characters).

**Resolution:** User configuration issue — not a code defect. The user should either:
- Select **Custom** provider with Base URL `https://openrouter.ai/api/v1` and their `sk-o...` key, **or**
- Obtain a genuine Minimax key from `https://platform.minimax.io`.

**L1 diagnostic tip:** If a user reports Minimax error 1004, ask them to check the key they entered. A Minimax key must start with `eyJ` and be at least 150 characters. An `sk-...` key is from a different provider.

---

#### Issue 5 — Gemini returns HTTP 429 rate limit on Generate Plan

**Symptom:** Gemini provider key validates successfully, but `POST /api/plan` returns 502 with "Gemini rate limit exceeded".

**Root cause:** Genuine Google API quota exhaustion. The Gemini free tier (`gemini-2.0-flash`) allows 15 requests/minute and 1,500 requests/day. Repeated testing within the same day or minute exhausts this quota.

**Resolution:** User/environment issue — not a code defect.
- Wait 60 seconds and retry if hitting the per-minute limit.
- If the daily limit is exhausted, wait until midnight Pacific time (Google quota reset).
- Switch to a paid Google AI Studio key with higher quotas for production use.
- Alternatively use the **Custom** provider with OpenRouter which provides free access to many models.

**Code improvement applied:** The 429 error message now tells the user the specific free-tier limits and suggests waiting or switching to a paid key. The Gemini 400 error now logs and surfaces the full response body to aid future diagnosis.

**Files changed:** `src/app/services/ai_provider.py`

**L1 diagnostic tip:** If a user reports Gemini rate limit errors, ask how many times they have clicked Generate Plan today. If more than ~10 times on a free key, the daily quota is likely exhausted.

---

#### Issue 6 — Claude provider authentication and plan generation working correctly

**Status:** Confirmed working as of 2026-03-10.

Claude (Anthropic) provider successfully authenticates and generates plans end-to-end with no issues. No code changes required for this provider in this session.

---

## 11. Support Escalation Checklist

Before escalating to L2 or L3, confirm the following have been attempted and documented:

- [ ] Python version confirmed as 3.11 or later
- [ ] `setup.bat` run successfully (no errors)
- [ ] `.env` file exists (copied from `.env.example`)
- [ ] Server starts with `start.bat` and shows startup message
- [ ] `GET /api/health` returns `{"status": "ok"}`
- [ ] API key validated successfully in the browser UI
- [ ] Exact error message captured (screenshot or copy)
- [ ] Terminal output captured from the Command Prompt window
- [ ] Issue is reproducible (i.e. happens every time, not just once)

Provide all of the above when raising a support ticket.

---

*Document maintained at `C:\saabdemo\app\docs\04-SUPPORT-TASKS.md`*
