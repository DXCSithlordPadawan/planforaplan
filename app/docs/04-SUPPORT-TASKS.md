# AI Application Generator — Support Tasks Guide

**Version:** 2.1
**Date:** 2026-03-10
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
11. [Known Issues and Fixes Log](#11-known-issues-and-fixes-log)
12. [Support Escalation Checklist](#12-support-escalation-checklist)

---

## 1. Support Tiers

| Tier | Scope | Who Handles |
|------|-------|-------------|
| L1 | User-facing issues: API key errors, browser not opening, provider configuration questions | Help desk / end-user support |
| L2 | Server and environment issues: ports blocked, dependencies missing, base template broken, startup failures | System administrator / DevOps |
| L3 | Code defects, AI provider integration failures, security incidents, architecture changes | Developer / application owner |

---

## 2. Diagnostic First Steps

Before investigating any issue, collect the following:

1. **Operating system and version** — `winver` on Windows
2. **Python version** — `.venv\Scripts\python.exe --version`
3. **Application version** — check `pyproject.toml`, field `version` (current: 2.0.0)
4. **Which AI provider is in use** — Claude, Gemini, Minimax, or Custom
5. **What the user was doing** — which step in the workflow failed
6. **Exact error message** — from the browser UI and/or terminal window
7. **Terminal output** — screenshot or copy of the Command Prompt/PowerShell showing the server log

---

## 3. L1 — Common User Issues

### 3.1 "Provider not configured" message in the browser

**Cause:** The user has not submitted their API key, or the page was reloaded clearing the in-memory state.

**Resolution:**
1. Ask the user to re-enter their API key in the configuration panel.
2. Select the correct provider from the dropdown.
3. Click **Validate & Save** and confirm the green tick appears.

---

### 3.2 "Invalid API key" / "Invalid Claude API key"

**Cause:** The key was typed incorrectly, contains spaces, or has been revoked.

**Resolution:**
1. Ask the user to copy the key directly from their provider console.
2. Confirm the selected provider matches the key type:
   - Claude keys start with `sk-ant-`
   - Gemini keys start with `AIzaSy`
   - Minimax keys start with `eyJ` and are 150+ characters
3. If revoked, the user must generate a new key.

---

### 3.3 "Gemini rate limit exceeded"

**Cause:** Google Gemini free tier is limited to 15 requests/minute and 1,500 requests/day.

**Resolution:**
1. If per-minute limit: wait 60 seconds and retry.
2. If daily limit exhausted: wait until midnight Pacific time or switch to a paid Gemini key.
3. Alternatively, switch to the **Custom** provider type with OpenRouter which offers free access to many models.

**L1 diagnostic tip:** If a user reports Gemini rate limit errors, ask how many times they have used it today. More than ~10 uses on a free key likely means the daily quota is exhausted.

---

### 3.4 Minimax returns error 1004 "login fail"

**Cause:** The user has entered an OpenRouter key (`sk-o...`) or other non-Minimax key in the Minimax provider field.

**Resolution:** A genuine Minimax key must be obtained from `platform.minimax.io`, starts with `eyJ`, and is 150+ characters. Instruct the user to either:
- Obtain a real Minimax key from `platform.minimax.io`, **or**
- Select **Custom** provider with Base URL `https://openrouter.ai/api/v1` and their `sk-o...` key.

---

### 3.5 Browser does not open automatically after deployment

**Cause:** `webbrowser.open()` failed silently (no default browser set, or sandboxed environment).

**Resolution:**
1. Ask the user to navigate manually to `http://127.0.0.1:8001`.
2. Check the terminal for any error after `"Browser launched"`.
3. Confirm a default browser is set in system settings.

---

### 3.6 Generation appears to hang at the same percentage

**Cause:** The AI API call is in progress. Large 32K-token generations can take 2–5 minutes. The heartbeat task keeps the progress indicator alive during this time — hanging progress is normal.

**Resolution:**
1. Advise the user to wait up to 5 minutes for the AI response.
2. If after 5 minutes there is no progress, ask the user to click **Cancel** and retry.
3. If retries fail consistently, escalate to L2 to check network and API connectivity.

---

### 3.7 "[Template warning] AI did not generate templates/index.html"

**Cause:** The AI omitted the landing page template from its output. The generated app may show a stub page or HTTP 500.

**Resolution:**
1. Ask the user to click Cancel and return to the plan view.
2. In the plan, add an explicit note: "The templates/index.html page must contain real visible HTML content."
3. Regenerate. If it recurs, escalate to L3 for prompt review.

---

### 3.8 Generated application shows "Internal Server Error" or blank page

**Cause:** The AI-generated code has a bug or syntax error.

**Resolution:**
1. Ask the user to go back, edit the plan to be more explicit, and regenerate.
2. Alternatively, advise the user to check `generated-apps\latest\main.py` for obvious errors.
3. If this recurs with the same requirement, escalate to L3 for prompt engineering review.

---

## 4. L2 — Application and Server Issues

### 4.1 `start.bat` / `start.ps1` fails with "Virtual environment not found"

**Cause:** `setup.bat` or `setup.ps1` was not run, or it failed partway through.

**Resolution:**
```cmd
cd C:\planforaplan
setup.bat
```
or
```powershell
cd C:\planforaplan
.\setup.ps1
```
Watch for error messages. Common failures:
- Python not in PATH → install Python 3.11+ and ensure "Add to PATH" was checked
- pip install failure → check internet connectivity; try upgrading pip first

---

### 4.2 Server starts but browser cannot reach `http://127.0.0.1:8000`

**Cause:** Firewall blocking port 8000, or server crashed at startup.

**Resolution:**
1. Check the terminal for `"AI Application Generator starting on http://127.0.0.1:8000"`. If absent, the server crashed.
2. Check Windows Firewall or corporate security software.
3. Test via terminal:
   ```cmd
   curl http://127.0.0.1:8000/api/health
   ```
4. If firewall is blocking, add an inbound rule for TCP port 8000 (local only).

---

### 4.3 Port 8001 is already in use

**Cause:** A previous generated application process did not terminate cleanly.

**Automatic resolution:** The orchestrator attempts to kill the process on port 8001 via psutil before each generation.

**Manual resolution:**
```cmd
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

---

### 4.4 Base template `.venv` is broken or missing packages

**Resolution:**
```cmd
cd C:\planforaplan\base-template
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\pip.exe install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
```

---

### 4.5 `provider shows as "not configured" after config save` / hot-reload wiping state

**Cause:** If uvicorn is started with `--reload`, hot-reload restarts the worker process on file-system changes, wiping the module-level `_provider` global in `state.py`. The official start scripts (`start.bat`, `start.ps1`, `start.sh`) do **not** use `--reload` for this reason.

**Resolution:** Confirm the server was started using the official start scripts, not a manual uvicorn command with `--reload`. Restart using `start.bat` or `.\start.ps1`.

---

### 4.6 Configuration changes in `.env` are not taking effect

**Cause:** The server was not restarted after editing `.env`.

**Resolution:** Stop the server (Ctrl+C), edit `.env`, and run the start script again.

---

### 4.7 Generated app fails to start: `No module named 'fastapi'`

**Cause:** The `base-template/.venv/` is missing or broken. The `install_requirements` function in the orchestrator only installs *extra* packages beyond the base set; if the base venv is missing, core packages are unavailable.

**Resolution:** Rebuild the base template venv (Section 4.4 above).

---

## 5. L3 — Code-Level Issues

### 5.1 AI response consistently returns no XML file blocks

**Symptom:** WebSocket shows `"No files were extracted from the AI response."` on every attempt.

**Investigation:**
1. Enable DEBUG logging: set `LOG_LEVEL=DEBUG` in `.env` and restart.
2. The full AI response will be logged. Confirm whether the AI is wrapping files in `<file path="...">` tags.
3. Check `prompts.py` `CODE_SYSTEM_PROMPT` — the XML format instructions and pre-flight checklist must be present.

**Resolution:**
- If the AI model has changed its output format, update `parse_generated_files()` in `file_service.py`.
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
3. If uvicorn outputs a different string in a future release, update `wait_for_ready()` detection strings in `process_service.py`.

---

### 5.3 `ValueError: Streaming is required` error in logs

**Symptom:** `POST /api/plan` returns HTTP 502 with a ValueError about streaming.

**Cause:** The Anthropic SDK requires streaming when `max_tokens` exceeds a threshold. `ClaudeProvider` should use `messages.stream()` — check that `ai_provider.py` is using the streaming path, not `messages.create()`.

**Resolution:** Verify `ClaudeProvider.generate()` uses `async with self._client.messages.stream(...)` and not `await self._client.messages.create(...)`.

---

### 5.4 Generated app crashes with Pydantic ValidationError at startup

**Symptom:** `Process stdout closed before signalling readiness.` Logs show a Pydantic `ValidationError`.

**Common causes:**
- A `float` value (e.g. `0.5`) assigned to an `int`-typed Pydantic field. Fix: change the field type to `float | int` or change the value to a whole number.
- Generated code uses `.dict()` instead of `.model_dump()` (Pydantic v2 removed `.dict()`). Fix: replace all `.dict()` calls with `.model_dump()`.

Both rules are enforced in `CODE_SYSTEM_PROMPT`. If they recur, review the prompt rules section.

---

### 5.5 Generation stale timeout triggering mid-stream

**Symptom:** `"Error: generation timed out. Please retry."` appears while the AI stream is still active.

**Cause:** The `_heartbeat` task in `routes/api.py` is not calling `state.set_status()`, so `_phase_updated_at` is not being refreshed. Or `_STALE_TIMEOUT` in `state.py` has been reduced below 600 seconds.

**Resolution:** Verify:
1. `_heartbeat` in `routes/api.py` calls `state.set_status(...)` on every tick.
2. `_STALE_TIMEOUT` in `state.py` is `600.0`.
3. The `httpx.Timeout` on `ClaudeProvider._http_client` has `read=480.0`.

---

### 5.6 Security scan (`bandit`) reports a new HIGH finding

**Action required:** Do not deploy to production until resolved.

**Process:**
1. Run `test.bat` / `.\test.ps1` and review bandit output.
2. Identify the file and line number.
3. Fix the code or add `# nosec B<id>  # Justification: <reason>` for confirmed false positives.
4. Re-run to confirm the finding is resolved.
5. Update `07-SECURITY-COMPLIANCE.md`.

---

### 5.7 Dependency vulnerability found by `pip-audit`

**Process:**
1. Run `test.bat` / `.\test.ps1` and review pip-audit output.
2. CRITICAL/HIGH CVEs: update the affected package in `pyproject.toml` and re-run setup.
3. MEDIUM/LOW CVEs: document in `07-SECURITY-COMPLIANCE.md` and set a review date.
4. If no fix is available, document mitigating controls and escalate to the application owner.

---

## 6. Log Locations and Reading Logs

### Orchestrator Server Logs

Logs are written to **stdout** in the terminal window running the start script. They are not written to a file by default.

Log format:
```
2026-03-10 14:23:01 app.routes.api INFO Generation/deployment failed: Claude rate limit exceeded.
```

Fields: `timestamp | logger_name | level | message`

To increase verbosity: set `LOG_LEVEL=DEBUG` in `.env` and restart.

To capture logs to a file (Windows CMD):
```cmd
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 > app.log 2>&1
```

### WebSocket Logs (Browser)

The terminal panel in the Execution view shows `info`, `success`, and `error` messages broadcast during generation. These are the most user-visible logs.

### Generated App Logs

The generated app's stdout is piped into the orchestrator's readiness monitor and shown in the WebSocket panel during deployment. After the app is running, its logs are discarded. To capture them manually:
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
Expected: `{"status": "ok"}`

### Full System Check

```cmd
REM 1. Orchestrator responsive
curl http://127.0.0.1:8000/api/health

REM 2. Status endpoint working
curl http://127.0.0.1:8000/api/status

REM 3. Index page serving HTML
curl http://127.0.0.1:8000/

REM 4. Python and venv functional
.venv\Scripts\python.exe -c "import fastapi; import anthropic; import psutil; import certifi; print('OK')"

REM 5. Base template venv functional
base-template\.venv\Scripts\python.exe -c "import fastapi; import uvicorn; print('OK')"
```

---

## 8. Port Conflict Resolution

| Port | Service | Action if blocked |
|------|---------|-------------------|
| 8000 | AI Application Generator orchestrator | Change `APP_PORT` in `.env`; restart |
| 8001 | Generated application | Change `GENERATED_APP_PORT` in `.env`; orchestrator uses new port automatically |

**Finding what is on a port (Windows CMD):**
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

```cmd
.venv\Scripts\python.exe -c "
import fastapi, uvicorn, anthropic, httpx, certifi
import jinja2, pydantic, pydantic_settings
import dotenv, psutil, cryptography, multipart
print('All dependencies OK')
"
```

Check installed versions:
```cmd
.venv\Scripts\pip.exe list | findstr -i "fastapi uvicorn anthropic httpx certifi jinja2 pydantic psutil cryptography"
```

Check for outdated packages:
```cmd
.venv\Scripts\pip.exe list --outdated
```

---

## 10. Resetting to a Clean State

### Soft reset (clear in-memory state)

Stop and restart the server:
```cmd
Ctrl+C
start.bat
```
This clears provider, process handle, and WebSocket connections from memory.

### Reset generated apps

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

## 11. Known Issues and Fixes Log

### Session: 2026-03-10 — Nine Men's Morris debug session

The following defects were identified and resolved during AI generation of a Nine Men's Morris game application.

---

#### BUG-001 — Landing page showed base-template stub instead of generated content

**Symptom:** Generated app displayed the base template stub "This template will be replaced."
**Root cause:** AI generated `base.html` (Jinja2 layout) but omitted `templates/index.html`. No warning was raised.
**Fix:** Added `validate_required_templates()` in `file_service.py`; hardened `CODE_SYSTEM_PROMPT` with a mandatory pre-flight checklist.

---

#### BUG-002/003 — Template validator missed router files; prompt too weak

**Symptom:** `stories.html` and `tasks.html` still missing after BUG-001 fix.
**Root cause:** Validator only scanned `main.py`; prompt wording too soft.
**Fix:** Switched to `rglob("*.py")` to scan all Python files; rewrote prompt checklist to be explicit.

---

#### BUG-004 — Only 6 files generated (truncated output)

**Symptom:** AI produced 6 files then stopped.
**Root cause:** `max_tokens=8192` too small for a multi-file app.
**Fix:** Raised `max_tokens` to `32768` in `ClaudeProvider`.

---

#### BUG-005 — Wrong import paths in generated code

**Symptom:** `ImportError` on startup — `from app.routers import ...` failed.
**Root cause:** AI used package-style imports not matching the flat deploy layout.
**Fix:** Added CORRECT/WRONG import path examples to `CODE_SYSTEM_PROMPT`.

---

#### BUG-006 — `ValueError: Streaming is required`

**Symptom:** `POST /api/plan` returned HTTP 500.
**Root cause:** Anthropic SDK requires streaming for large `max_tokens`. Raising to 32768 triggered this.
**Fix:** Replaced `messages.create()` with `messages.stream()` in `ClaudeProvider.generate()`.

---

#### BUG-007 — Pydantic `float` → `int` validation error at startup

**Symptom:** `Process stdout closed before signalling readiness.`
**Root cause:** `estimated_hours=0.5` assigned to `int`-typed Pydantic field.
**Fix:** Patched generated app; added `float | int` rule to `CODE_SYSTEM_PROMPT`.

---

#### BUG-008 — Pydantic v2 `.dict()` removed

**Symptom:** `AttributeError` on any game API call.
**Root cause:** Pydantic v2 replaced `.dict()` with `.model_dump()`.
**Fix:** Patched generated app; added `.model_dump()` rule to `CODE_SYSTEM_PROMPT`.

---

#### BUG-009 — Generation timed out mid-stream

**Symptom:** `"Error: generation timed out. Please retry."` while AI stream was still active.
**Root cause:** `_heartbeat` not calling `state.set_status()`; 300s stale timeout too short; no httpx timeout.
**Fix:** Heartbeat now refreshes `_phase_updated_at` every second; `_STALE_TIMEOUT` raised to 600s; `httpx.Timeout(connect=10, read=480, write=30, pool=10)` added.

---

### Session: 2026-03-10 — Provider Configuration Fixes

---

#### ISSUE-1 — OpenRouter / Custom provider returns HTTP 429 on config save

**Symptom:** Configuring a free-tier OpenRouter model produced 429 immediately on *Validate & Save*.
**Root cause:** `POST /api/config` made a live probe call to validate the key. Free-tier models have very low rate limits; the probe call consumed the quota immediately.
**Fix:** Removed the probe call from `configure()` in `routes/api.py`. The provider is now stored immediately. Invalid keys surface naturally on first `/api/plan` or `/api/generate`.

---

#### ISSUE-2 — Provider shows as "not configured" after successful config save

**Symptom:** After *Validate & Save*, clicking *Generate Plan* returned "Provider not configured".
**Root cause:** Start scripts launched uvicorn with `--reload`. Hot-reload restarted the worker process on file-system changes, wiping `_provider = None`.
**Fix:** Removed `--reload` from `start.ps1`, `start.bat`, and `start.sh`. Comments added explaining why.

---

#### ISSUE-3 — Minimax returns HTTP 401 "Invalid API key"

**Root cause:** `MinimaxProvider.API_URL` was set to the old `api.minimax.chat` domain (no longer active). Current host is `api.minimax.io`. Additionally the OpenAI-compat path was used instead of the native `/v1/text/chatcompletion_v2` endpoint.
**Fix:** Updated `MinimaxProvider` to use `API_BASE = "https://api.minimax.io"` and `API_PATH = "/v1/text/chatcompletion_v2"`.

---

#### ISSUE-4 — Minimax error 1004 after endpoint fix

**Root cause:** User was entering an OpenRouter key in the Minimax provider field. See L1 Section 3.4 for the diagnostic and resolution.

---

#### ISSUE-5 — Gemini returns HTTP 429 rate limit on Generate Plan

**Root cause:** Genuine Google API quota exhaustion on the free tier.
**Resolution:** User/environment issue — not a code defect. See L1 Section 3.3 for guidance.
**Code improvement applied:** The 429 error message now quotes specific free-tier limits and suggests waiting or switching to a paid key. Gemini 400 responses now log and surface the full response body.

---

## 12. Support Escalation Checklist

Before escalating to L2 or L3, confirm the following have been attempted and documented:

- [ ] Python version confirmed as 3.11 or later
- [ ] `setup.bat` or `setup.ps1` run successfully (no errors)
- [ ] `.env` file exists (copied from `.env.example`)
- [ ] Server starts with `start.bat` / `.\start.ps1` and shows startup message
- [ ] `GET /api/health` returns `{"status": "ok"}`
- [ ] API key validated successfully in the browser UI
- [ ] Exact error message captured (screenshot or copy)
- [ ] Terminal output captured from the Command Prompt / PowerShell window
- [ ] Issue is reproducible (happens every time, not just once)

Provide all of the above when raising a support ticket.

---

*Document maintained at `C:\planforaplan\docs\04-SUPPORT-TASKS.md`*
