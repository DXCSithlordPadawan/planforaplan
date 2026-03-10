"""In-memory session state for the AI Application Generator.

Security note: API keys submitted through the browser UI are stored here
in process memory only. They are never written to disk or logged.

Concurrency note: FastAPI runs handlers in an async event loop (single thread
for async routes). asyncio.Lock guards shared mutable state.
"""

import asyncio
import logging
import subprocess
import time
from typing import Any

logger = logging.getLogger(__name__)

# --- Internal state -----------------------------------------------------------

_lock = asyncio.Lock()

_provider: Any = None          # AIProvider instance (set after /api/config)
_process: subprocess.Popen | None = None   # Running generated-app process
_phase: str = "idle"           # idle | planning | generating | deploying | running
_progress: int = 0             # 0-100
_message: str = "Ready"
_server_url: str | None = None
_websockets: list[Any] = []    # Connected WebSocket clients
_phase_updated_at: float = 0.0  # monotonic timestamp of last set_status call

# Phases considered "in-progress" — auto-reset after STALE_TIMEOUT seconds
_ACTIVE_PHASES = frozenset({"generating", "deploying"})
_STALE_TIMEOUT: float = 300.0  # 5 minutes


# --- Provider -----------------------------------------------------------------

def set_provider(provider: Any) -> None:
    """Store the configured AI provider instance."""
    global _provider
    _provider = provider
    logger.info("AI provider configured: %s", type(provider).__name__)


def get_provider() -> Any | None:
    """Return the configured AI provider, or None if not yet set."""
    return _provider


# --- Process ------------------------------------------------------------------

def set_process(process: subprocess.Popen | None) -> None:
    """Store a reference to the running generated-app subprocess."""
    global _process
    _process = process


def get_process() -> subprocess.Popen | None:
    """Return the currently running subprocess, or None."""
    return _process


# --- Execution status ---------------------------------------------------------

def set_status(phase: str, progress: int, message: str, url: str | None = None) -> None:
    """Update the current execution phase, progress, and message."""
    global _phase, _progress, _message, _server_url, _phase_updated_at
    _phase = phase
    _progress = max(0, min(100, progress))
    _message = message
    _server_url = url
    _phase_updated_at = time.monotonic()
    logger.debug("Status: phase=%s progress=%d msg=%s", phase, progress, message)


def get_status() -> dict[str, Any]:
    """Return the current execution status as a plain dict.

    If an active phase (generating/deploying) has not been updated for longer
    than _STALE_TIMEOUT seconds, the status is auto-reset to 'idle' with an
    error message.  This prevents the UI from being permanently stuck after a
    silent background task failure.
    """
    global _phase, _progress, _message, _server_url, _phase_updated_at
    if (
        _phase in _ACTIVE_PHASES
        and _phase_updated_at > 0
        and (time.monotonic() - _phase_updated_at) > _STALE_TIMEOUT
    ):
        logger.warning(
            "Generation phase '%s' has been stale for >%.0fs — auto-resetting.",
            _phase,
            _STALE_TIMEOUT,
        )
        _phase = "idle"
        _progress = 0
        _message = "Error: generation timed out. Please retry."
        _server_url = None
    return {
        "phase": _phase,
        "progress": _progress,
        "message": _message,
        "url": _server_url,
    }


# --- WebSocket connections ----------------------------------------------------

def register_websocket(ws: Any) -> None:
    """Add a WebSocket client to the broadcast list."""
    _websockets.append(ws)
    logger.debug("WebSocket registered. Total: %d", len(_websockets))


def unregister_websocket(ws: Any) -> None:
    """Remove a WebSocket client from the broadcast list."""
    if ws in _websockets:
        _websockets.remove(ws)
    logger.debug("WebSocket removed. Total: %d", len(_websockets))


async def broadcast(level: str, message: str) -> None:
    """Send a log message JSON to all connected WebSocket clients."""
    import json

    payload = json.dumps({"level": level, "message": message})
    dead: list[Any] = []
    for ws in list(_websockets):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        unregister_websocket(ws)
