from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any
import json

app = FastAPI(title="Nine Men's Morris - User Stories")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# In-memory storage for user stories
USER_STORIES = [
    {
        "id": "US001",
        "title": "View Game Landing Page",
        "description": "As a player, I want to see a clean dark-themed landing page so that I can understand what the game is about and start playing.",
        "acceptance_criteria": [
            "Landing page displays game title and description",
            "Dark theme is applied consistently",
            "Navigation to game and user stories is available",
            "Page is responsive on different screen sizes"
        ],
        "priority": "High",
        "epic": "User Interface",
        "story_points": 3
    },
    {
        "id": "US002", 
        "title": "Start New Game",
        "description": "As a player, I want to start a new Nine Men's Morris game so that I can begin playing against another player.",
        "acceptance_criteria": [
            "New game button is clearly visible",
            "Game board is initialized with empty positions", 
            "Player 1 starts the game",
            "Game phase is set to placement"
        ],
        "priority": "High",
        "epic": "Game Core",
        "story_points": 5
    },
    {
        "id": "US003",
        "title": "Place Game Pieces",
        "description": "As a player, I want to place my pieces on the board during the placement phase so that I can set up my strategy.",
        "acceptance_criteria": [
            "Can click on empty board positions to place pieces",
            "Pieces are visually distinct for each player",
            "Cannot place pieces on occupied positions",
            "Turn alternates between players automatically"
        ],
        "priority": "High", 
        "epic": "Game Core",
        "story_points": 8
    },
    {
        "id": "US004",
        "title": "Move Game Pieces",
        "description": "As a player, I want to move my pieces to adjacent positions during the movement phase so that I can form mills and capture opponent pieces.",
        "acceptance_criteria": [
            "Can select own pieces to move",
            "Can move pieces to adjacent empty positions",
            "Invalid moves are prevented with visual feedback",
            "Movement rules are enforced correctly"
        ],
        "priority": "High",
        "epic": "Game Core", 
        "story_points": 10
    },
    {
        "id": "US005",
        "title": "Form Mills",
        "description": "As a player, I want to form mills (three pieces in a row) so that I can capture opponent pieces and gain advantage.",
        "acceptance_criteria": [
            "Mills are detected automatically (horizontal, vertical, diagonal)",
            "Mill formation triggers capture phase",
            "Visual indication when mill is formed",
            "Mill positions are highlighted"
        ],
        "priority": "High",
        "epic": "Game Logic",
        "story_points": 8
    },
    {
        "id": "US006",
        "title": "Capture Opponent Pieces",
        "description": "As a player, I want to capture opponent pieces when I form a mill so that I can reduce their pieces and win the game.",
        "acceptance_criteria": [
            "Can select opponent piece to capture after forming mill",
            "Cannot capture pieces that are part of a mill (unless no other option)",
            "Captured pieces are removed from board",
            "Capture count is updated"
        ],
        "priority": "High",
        "epic": "Game Logic",
        "story_points": 6
    },
    {
        "id": "US007",
        "title": "Flying Phase Movement",
        "description": "As a player, I want to move my pieces to any empty position when I have only 3 pieces left so that I can continue playing with increased mobility.",
        "acceptance_criteria": [
            "Flying phase activates when player has 3 pieces",
            "Can move pieces to any empty position on board",
            "Flying rules override normal adjacency requirements",
            "Visual indication of flying phase"
        ],
        "priority": "Medium",
        "epic": "Game Logic",
        "story_points": 5
    },
    {
        "id": "US008",
        "title": "Win Condition Detection",
        "description": "As a player, I want the game to detect when I win so that the game ends appropriately and declares the winner.",
        "acceptance_criteria": [
            "Game ends when opponent has less than 3 pieces",
            "Game ends when opponent cannot make valid moves",
            "Winner is clearly displayed",
            "Option to start new game is provided"
        ],
        "priority": "High",
        "epic": "Game Logic",
        "story_points": 4
    },
    {
        "id": "US009",
        "title": "Game State Display",
        "description": "As a player, I want to see the current game state and whose turn it is so that I can understand the game progress.",
        "acceptance_criteria": [
            "Current player turn is displayed",
            "Game phase (placement/movement/flying) is shown",
            "Piece count for each player is visible",
            "Game status updates in real-time"
        ],
        "priority": "Medium",
        "epic": "User Interface",
        "story_points": 3
    },
    {
        "id": "US010",
        "title": "Visual Feedback for Moves",
        "description": "As a player, I want visual feedback for my moves and game events so that I can understand what's happening in the game.",
        "acceptance_criteria": [
            "Valid positions are highlighted when selecting pieces",
            "Invalid moves show error indicators",
            "Animations for piece placement and movement",
            "Mill formations are visually emphasized"
        ],
        "priority": "Medium",
        "epic": "User Interface",
        "story_points": 6
    },
    {
        "id": "US011",
        "title": "Responsive Game Board",
        "description": "As a player, I want the game board to be responsive and work well on different screen sizes so that I can play on various devices.",
        "acceptance_criteria": [
            "Game board scales appropriately on mobile devices",
            "Touch interactions work on mobile",
            "UI elements remain accessible at different sizes",
            "Text and buttons are readable on all screen sizes"
        ],
        "priority": "Medium",
        "epic": "User Interface",
        "story_points": 5
    },
    {
        "id": "US012",
        "title": "Dark Theme Consistency",
        "description": "As a player, I want a consistent dark theme throughout the application so that I have a pleasant visual experience.",
        "acceptance_criteria": [
            "All pages use consistent dark color scheme",
            "Text contrast meets accessibility standards",
            "Interactive elements have appropriate hover states",
            "Theme remains consistent across all components"
        ],
        "priority": "Low",
        "epic": "User Interface",
        "story_points": 3
    },
    {
        "id": "US013",
        "title": "View User Stories",
        "description": "As a business analyst, I want to view all user stories for the Nine Men's Morris game so that I can track development progress and requirements.",
        "acceptance_criteria": [
            "User stories are displayed in a clean, organized format",
            "Stories are categorized by epic",
            "Each story shows title, description, acceptance criteria, and priority",
            "Story points are visible for estimation purposes"
        ],
        "priority": "High",
        "epic": "Project Management",
        "story_points": 4
    },
    {
        "id": "US014",
        "title": "Game Rules Display",
        "description": "As a new player, I want to see the rules of Nine Men's Morris so that I can learn how to play the game.",
        "acceptance_criteria": [
            "Rules are accessible from the main interface",
            "Rules explain all three game phases clearly",
            "Visual examples accompany rule explanations",
            "Rules can be closed to return to game"
        ],
        "priority": "Low",
        "epic": "User Interface",
        "story_points": 4
    },
    {
        "id": "US015",
        "title": "Move History Tracking",
        "description": "As a player, I want to see a history of moves made in the game so that I can review the game progression.",
        "acceptance_criteria": [
            "Move history is displayed in chronological order",
            "Each move shows player, action, and positions",
            "History updates automatically after each move",
            "History can be scrolled if it becomes long"
        ],
        "priority": "Low",
        "epic": "Game Features",
        "story_points": 5
    }
]

# Game connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/user-stories", response_class=HTMLResponse)
async def user_stories_page(request: Request):
    # Group stories by epic
    epics = {}
    for story in USER_STORIES:
        epic = story["epic"]
        if epic not in epics:
            epics[epic] = []
        epics[epic].append(story)
    
    return templates.TemplateResponse("user_stories.html", {
        "request": request,
        "epics": epics,
        "total_stories": len(USER_STORIES)
    })

@app.get("/api/user-stories")
async def get_user_stories():
    return {"user_stories": USER_STORIES}

@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Game update: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)