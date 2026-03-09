"""WebSocket endpoint for real-time log streaming.

Clients connect to /ws/logs and receive JSON messages:
  {"level": "info"|"success"|"error", "message": "..."}

The connection is registered in app.state and receives all broadcast()
calls during generation and deployment.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import state

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """Accept and maintain a WebSocket log-streaming connection."""
    await websocket.accept()
    state.register_websocket(websocket)
    logger.debug("WebSocket client connected")

    try:
        # Keep the connection open by receiving (and ignoring) keep-alive pings
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    finally:
        state.unregister_websocket(websocket)
