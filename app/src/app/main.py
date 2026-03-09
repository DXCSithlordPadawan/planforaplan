"""FastAPI application factory for the AI Application Generator.

Creates and configures the FastAPI app with:
  - Security headers middleware (OWASP A05, CIS Benchmark L2)
  - CORS middleware restricted to localhost
  - REST API routes (/api/*)
  - WebSocket route (/ws/logs)
  - Static file serving (/static)
  - Jinja2 template rendering for the browser UI
  - GET / — serves the single-page HTML interface
"""

import logging
import logging.config
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.routes import api, websocket

logger = logging.getLogger(__name__)

# Paths relative to this file
_SRC_DIR = Path(__file__).parent
_TEMPLATES_DIR = _SRC_DIR / "templates"
_STATIC_DIR = _SRC_DIR / "static"


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security response headers to every reply.

    Implements OWASP A05 (Security Misconfiguration) controls and
    CIS Benchmark Level 2 HTTP header hardening.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
            "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
            "font-src https://fonts.gstatic.com; "
            f"connect-src 'self' "
            f"ws://{settings.app_host}:{settings.app_port} "
            f"ws://localhost:{settings.app_port};"
        )
        return response


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and return the configured FastAPI application."""

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    app = FastAPI(
        title="AI Application Generator",
        version="2.0.0",
        description="Generate and deploy Python web apps from natural language.",
        docs_url="/docs",
        redoc_url=None,
    )

    # --- Middleware -----------------------------------------------------------
    app.add_middleware(SecurityHeadersMiddleware)
    # Build CORS allowed origins from configured host/port.
    # 0.0.0.0 is a bind address (all interfaces), not a valid browser origin;
    # skip it so browsers can still issue same-origin requests when the server
    # is accessed via localhost or a real hostname behind a reverse proxy.
    _cors_origins = {
        f"http://localhost:{settings.app_port}",
        f"http://127.0.0.1:{settings.app_port}",
    }
    if settings.app_host not in ("0.0.0.0", ""):
        _cors_origins.add(f"http://{settings.app_host}:{settings.app_port}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # --- Routes --------------------------------------------------------------
    app.include_router(api.router, prefix="/api", tags=["api"])
    app.include_router(websocket.router, tags=["websocket"])

    # --- Static files --------------------------------------------------------
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # --- Jinja2 templates ----------------------------------------------------
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        """Serve the single-page HTML interface."""
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "app_port": settings.app_port,
                "generated_app_port": settings.generated_app_port,
            },
        )

    logger.info(
        "AI Application Generator starting on http://%s:%d",
        settings.app_host,
        settings.app_port,
    )
    return app


# Module-level app instance used by uvicorn
app = create_app()
