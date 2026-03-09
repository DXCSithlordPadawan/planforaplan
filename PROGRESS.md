# AI Application Generator - Progress Tracker

**Project:** AI Application Generator v2.0  
**Tech Stack:** Python 3.11+ / FastAPI  
**Last Updated:** March 6, 2026  
**Tracking Location:** C:\saabdemo\PROGRESS.md

---

## Current Status

| Item | Status |
|------|--------|
| Documentation refactor (Node.js → Python) | ✅ Complete |
| PRD v2.0 | ✅ Complete |
| Implementation Plan v2.0 | ✅ Complete |
| README v2.0 | ✅ Complete |
| Phase 1: Foundation Setup | ✅ Complete |
| Phase 2: AI Integration | ✅ Complete |
| Phase 3: Process Management | ✅ Complete |
| Phase 4: Frontend Development | ✅ Complete |
| Phase 5: Testing & Containerisation | ✅ Complete (structure) |
| **Awaiting:** venv install + runtime test | ⏳ Manual step required |

---

## Completed Milestones

### March 6, 2026 — Documentation Refactor v2.0
All planning documents updated from Node.js/Express stack to Python/FastAPI.

### March 6, 2026 — Implementation v2.0 (C:\saabdemo\app)

All application artefacts written to `C:\saabdemo\app\`.

**Files created:**

```
C:\saabdemo\app\
├── pyproject.toml                          # Project dependencies + tooling config
├── .env.example                            # Environment variable template
├── .gitignore
├── Containerfile                           # Podman build file (non-root, HEALTHCHECK)
├── setup.bat                               # Windows: creates venv, installs deps
├── start.bat                               # Windows: starts orchestrator
├── test.bat                                # Windows: runs pytest + bandit + pip-audit
├── src\app\
│   ├── __init__.py
│   ├── main.py                             # FastAPI app factory, security middleware
│   ├── config.py                           # pydantic-settings configuration
│   ├── state.py                            # In-memory session state + WS broadcast
│   ├── prompts.py                          # AI system prompts (plan + code gen)
│   ├── models\
│   │   ├── __init__.py                     # Pydantic v2 schemas (all endpoints)
│   │   └── schemas.py
│   ├── routes\
│   │   ├── __init__.py
│   │   ├── api.py                          # REST endpoints: config/plan/generate/status/stop
│   │   └── websocket.py                    # WebSocket /ws/logs endpoint
│   ├── services\
│   │   ├── __init__.py
│   │   ├── ai_provider.py                  # Claude + Minimax providers + factory
│   │   ├── file_service.py                 # Template copy, file write, XML parser
│   │   └── process_service.py              # psutil port mgmt, uvicorn launch, browser
│   └── templates\
│       └── index.html                      # Full single-page UI (all 4 views)
├── base-template\                          # Pre-installed generated-app template
│   ├── main.py
│   ├── requirements.txt
│   ├── templates\index.html
│   └── static\style.css
└── tests\
    ├── __init__.py
    ├── conftest.py
    ├── test_file_service.py                # CWE-22 path traversal + parser tests
    ├── test_api.py                         # REST endpoint integration tests
    └── test_ai_provider.py                 # Provider factory unit tests
```

---

## Security Controls Implemented

| Control | Location | Standard |
|---------|----------|----------|
| Path traversal prevention (`Path.resolve()`) | `file_service.py` | CWE-22 |
| Command injection prevention (list-form subprocess) | `process_service.py` | CWE-78 |
| Input validation (Pydantic v2 schemas) | `models/__init__.py` | OWASP A03 |
| Security response headers middleware | `main.py` | OWASP A05, CIS L2 |
| API key in-memory only (never logged/persisted) | `state.py`, `ai_provider.py` | NIST IA-5 |
| CORS restricted to localhost origin | `main.py` | OWASP A05 |
| Non-root container user | `Containerfile` | CIS Benchmark L2 |
| Container HEALTHCHECK | `Containerfile` | CIS Benchmark L2 |

---

## Open Issues / Gaps to Address

| # | Issue | Priority | Notes |
|---|-------|----------|-------|
| 1 | `state.py` in-memory session not thread-safe under concurrent requests | Medium | `asyncio.Lock` in place for async; sync access from thread executor needs review |
| 2 | `wait_for_ready()` reads stdout in a thread executor — blocks thread pool | Medium | Consider async subprocess with `asyncio.subprocess` for full async readiness check |
| 3 | Base template `.venv/` will not be portable between Python versions | Medium | Document Python version pinning; the venv Python must match orchestrator Python |
| 4 | Tailwind CDN not available in air-gapped environments | Low | Provide Tailwind CLI binary alternative in docs |
| 5 | Generated app does not have its own security review | Medium | Add `bandit` scan of generated code before first run |
| 6 | `setup.bat` / `start.bat` use Windows paths only | Low | Add `setup.sh` / `start.sh` for Linux/macOS users |

---

## Manual Steps Required Before First Run

1. **Install Python 3.11+** on the host machine (https://python.org)
2. **Run `setup.bat`** from `C:\saabdemo\app\` — creates `.venv`, installs all dependencies, pre-installs base template venv
3. **Copy `.env.example` to `.env`** — adjust paths if needed (defaults should work)
4. **Run `start.bat`** — starts the orchestrator on `http://127.0.0.1:8000`
5. **Open browser** to `http://127.0.0.1:8000`
6. **Enter API key** in the configuration panel, click "Validate & Save"
7. **Enter requirement**, click "Generate Plan", review, submit

---

## Version History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | March 6, 2026 | Iain Reid | Initial documentation (Node.js stack) |
| 2.0 | March 6, 2026 | Iain Reid | Full refactor to Python/FastAPI stack with security compliance |
| 2.1 | March 6, 2026 | Iain Reid | Full implementation artefacts written to C:\saabdemo\app |
