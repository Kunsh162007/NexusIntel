"""
WebSocket + REST endpoints for the Auto-Focus Engine.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse

from models import WatchListItem, DemoScenarioRequest, Track

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/engine", tags=["engine"])


# ── WebSocket connection manager ──────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self._clients: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.add(ws)
        logger.info(f"WS client connected (total={len(self._clients)})")

    def disconnect(self, ws: WebSocket):
        self._clients.discard(ws)
        logger.info(f"WS client disconnected (total={len(self._clients)})")

    async def broadcast(self, message: dict):
        dead = set()
        for ws in self._clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self._clients -= dead


manager = ConnectionManager()


async def broadcast(message: dict):
    """Called by the engine to push events to all connected clients."""
    await manager.broadcast(message)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send engine status on connect
        from main import engine  # imported here to avoid circular
        await websocket.send_json(
            {"type": "status", "data": engine.get_status(), "timestamp": datetime.utcnow().isoformat()}
        )
        # Keep alive
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── REST endpoints ────────────────────────────────────────────────────────────

@router.get("/status")
async def get_engine_status():
    from main import engine
    return engine.get_status()


@router.post("/start")
async def start_engine():
    from main import engine
    engine.start()
    return {"message": "Engine started"}


@router.post("/stop")
async def stop_engine():
    from main import engine
    await engine.stop()
    return {"message": "Engine stopped"}


@router.get("/insights")
async def get_insights(track: Track | None = None, limit: int = 50):
    from main import engine
    insights = engine.get_insights(track=track, limit=limit)
    return [i.model_dump(mode="json") for i in insights]


@router.get("/watchlist")
async def get_watchlist():
    from main import engine
    return [item.model_dump(mode="json") for item in engine.get_watchlist()]


@router.post("/watchlist")
async def add_watch_item(item: WatchListItem):
    from main import engine
    engine.add_watch_item(item)
    return item.model_dump(mode="json")


@router.delete("/watchlist/{item_id}")
async def remove_watch_item(item_id: str):
    from main import engine
    engine.remove_watch_item(item_id)
    return {"message": f"Watch item {item_id} removed"}


@router.post("/demo")
async def run_demo(request: DemoScenarioRequest):
    """Trigger a pre-built demo scenario without waiting for a real anomaly."""
    from main import engine
    brief = await engine.run_demo_scenario(request.scenario)
    return brief.model_dump(mode="json")


@router.get("/trigger-stats")
async def get_trigger_stats():
    from main import trigger_client
    return trigger_client.get_stats()
