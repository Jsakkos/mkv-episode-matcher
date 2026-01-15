from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from mkv_episode_matcher.backend.socket_manager import get_manager

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    from loguru import logger
    logger.info("WebSocket connection attempt")
    manager = get_manager()
    await manager.connect(websocket)
    logger.info("WebSocket connected")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected")
