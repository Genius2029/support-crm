import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import verify_token
from app.database import engine
from app.models.manager import Manager
from app.websocket.manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # await for token 10s not more
    try:
        token = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        manager_id = verify_token(token)
        async with AsyncSession(engine) as session:
            result = await session.execute(select(Manager).where(Manager.id == manager_id))
            if not result.scalars().first():
                raise ValueError("Manager not found")
    except Exception:
        with contextlib.suppress(Exception):
            await websocket.close(code=1008)
        return

    ws_manager.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.remove(websocket)