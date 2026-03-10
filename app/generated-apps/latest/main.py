from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from app.routers import game_routes, planning_routes
from app.services.planning_service import PlanningService

app = FastAPI(title="Nine Men Morris - Project Planning Tool")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize planning service
planning_service = PlanningService()

# Include routers
app.include_router(game_routes.router, prefix="/game", tags=["game"])
app.include_router(planning_routes.router, prefix="/planning", tags=["planning"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})

@app.get("/epics", response_class=HTMLResponse)
async def epics_page(request: Request):
    epics = planning_service.get_epics()
    return templates.TemplateResponse("epics.html", {"request": request, "epics": epics})

@app.get("/stories", response_class=HTMLResponse)
async def stories_page(request: Request):
    stories = planning_service.get_user_stories()
    epics = planning_service.get_epics()
    return templates.TemplateResponse("stories.html", {"request": request, "stories": stories, "epics": epics})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    tasks = planning_service.get_tasks()
    stories = planning_service.get_user_stories()
    return templates.TemplateResponse("tasks.html", {"request": request, "tasks": tasks, "stories": stories})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)