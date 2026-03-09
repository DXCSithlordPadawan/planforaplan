"""Minimal FastAPI base template application.

This is the pre-installed template that gets copied for every generated app.
The virtual environment (.venv/) in this directory should have fastapi,
uvicorn[standard], and jinja2 pre-installed.

Generated apps overwrite main.py, requirements.txt, and the templates/
directory with AI-generated content.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Generated Application")

_BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(_BASE / "templates"))

if (_BASE / "static").exists():
    app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve the generated application home page."""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
