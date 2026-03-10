# AI Application Generator — Bug Fix Log

**Project:** `C:\planforaplan`
**Session date:** 2026-03-10
**Status:** All issues resolved — generator working correctly.

---

## BUG-001 — Landing page showed base-template stub instead of generated content

**Symptom:** Generated app displayed *"Base Template — This template will be replaced."*
**Root cause:** `copy_base_template()` always writes stub `index.html` first. AI generated `base.html` (a Jinja2 layout skeleton) but omitted `templates/index.html`, leaving the stub in place. No warning raised.
**Files changed:**
- `src/app/prompts.py` — Clarified `templates/index.html` must be the real rendered landing page.
- `src/app/services/file_service.py` — Added `validate_required_templates()` to warn when `index.html` or any `TemplateResponse()` target is missing.
- `src/app/routes/api.py` — Wired validation into deployment pipeline; warnings broadcast to UI log panel.

---

## BUG-002 — Template validator missed router files

**Symptom:** `stories.html` and `tasks.html` missing; their `TemplateResponse()` calls were in `routers/` not `main.py`.
**Root cause:** `validate_required_templates()` only scanned `main.py`.
**Files changed:**
- `src/app/services/file_service.py` — Switched to `rglob("*.py")` to scan all Python files in deploy directory.

---

## BUG-003 — AI prompt too weak; templates still omitted after BUG-001

**Symptom:** AI continued omitting `index.html` and child templates.
**Root cause:** Soft wording in `CODE_SYSTEM_PROMPT` — AI treated `base.html` as satisfying the `index.html` requirement.
**Files changed:**
- `src/app/prompts.py` — Added explicit 4-point pre-flight checklist; named the exact failure mode; stated missing templates cause HTTP 500.

---

## BUG-004 — Only 6 files generated; truncated output

**Symptom:** AI produced 6 files then stopped; several templates never appeared.
**Root cause:** `max_tokens=8192` too small for a multi-file app with 5+ templates, services, and routers.
**Files changed:**
- `src/app/services/ai_provider.py` — Raised `max_tokens` from `8192` to `32768`.

---

## BUG-005 — Wrong import paths in generated code

**Symptom:** `ImportError` on startup — `from app.routers import ...` failed; no `app/` package in deploy directory.
**Root cause:** AI defaulted to package-style imports not matching the flat deploy layout.
**Files changed:**
- `src/app/prompts.py` — Added explicit CORRECT/WRONG import path examples to `CODE_SYSTEM_PROMPT`.

---

## BUG-006 — `ValueError: Streaming is required`

**Symptom:** `POST /api/plan` returned HTTP 500.
**Root cause:** Anthropic SDK requires streaming when `max_tokens` exceeds a threshold. Raising to `32768` (BUG-004) tripped this.
**Files changed:**
- `src/app/services/ai_provider.py` — Replaced `messages.create()` with `messages.stream()`; collects all `text_delta` events and returns as single string.

---

## BUG-007 — Generated app crashed at startup (Pydantic `float` to `int` error)

**Symptom:** `Process stdout closed before signalling readiness.`
**Root cause:** `estimated_hours=0.5` assigned to a Pydantic `int` field. Pydantic v2 raises `ValidationError` at import time.
**Files changed:**
- `generated-apps/latest/services/story_service.py` — Changed `estimated_hours=0.5` to `1` (one-time patch).
- `src/app/prompts.py` — Added rule: use `float | int` for fields that may hold decimal values.

---

## BUG-008 — Generated app crashed (Pydantic v2 `.dict()` removed)

**Symptom:** `AttributeError` on any game API call.
**Root cause:** Pydantic v2 replaced `.dict()` with `.model_dump()`. AI generated v1-style calls.
**Files changed:**
- `generated-apps/latest/routes/game_routes.py` — Replaced all `.dict()` calls with `.model_dump()` (one-time patch).
- `src/app/prompts.py` — Added rule: use `.model_dump()` not `.dict()`; do not pin pydantic in `requirements.txt`.

---

## BUG-009 — Generation timed out: `generation timed out. Please retry.`

**Symptom:** UI showed timeout error while AI stream was still actively running.
**Root cause 1:** `_heartbeat` coroutine sent UI messages but never called `state.set_status()`, so `_phase_updated_at` was not refreshed. The 300s stale guard fired mid-stream.
**Root cause 2:** 300s stale timeout too short for 32K-token responses.
**Root cause 3:** No timeout on `httpx` streaming client — a stalled stream could hang indefinitely.
**Files changed:**
- `src/app/routes/api.py` — `_heartbeat` now calls `state.set_status()` every tick to keep `_phase_updated_at` current.
- `src/app/state.py` — Raised `_STALE_TIMEOUT` from `300s` to `600s`.
- `src/app/services/ai_provider.py` — Added `httpx.Timeout(connect=10s, read=480s, write=30s, pool=10s)`.

---

## Canonical List of Modified Files

| File | Summary of changes |
|------|--------------------|
| `src/app/prompts.py` | Strengthened `CODE_SYSTEM_PROMPT`: index.html rules, checklist, import paths, Pydantic v2 rules |
| `src/app/services/ai_provider.py` | `max_tokens` 8192 to 32768; non-streaming to streaming; `httpx.Timeout` added |
| `src/app/services/file_service.py` | Added `validate_required_templates()`; scans all `.py` via `rglob` |
| `src/app/routes/api.py` | Template validation wired in; heartbeat refreshes stale-guard timestamp |
| `src/app/state.py` | `_STALE_TIMEOUT` 300s to 600s |
| `generated-apps/latest/services/story_service.py` | `estimated_hours=0.5` to `1` (one-time generated-app patch) |
| `generated-apps/latest/routes/game_routes.py` | `.dict()` to `.model_dump()` (one-time generated-app patch) |
