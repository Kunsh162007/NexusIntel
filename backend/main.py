"""
NexusIntel AI — FastAPI application entry point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
from engine.bright_data import BrightDataClient
from engine.auto_focus import AutoFocusEngine
from memory.knowledge_graph import KnowledgeGraph
from actions.triggers import TriggerClient
from voice.speech import SpeechmaticsClient, CommandParser
from routes.engine_routes import broadcast, router as engine_router
from routes.gtm import router as gtm_router
from routes.finance import router as finance_router
from routes.security import router as security_router
from routes.voice_routes import router as voice_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Global singletons ─────────────────────────────────────────────────────────

bright_data = BrightDataClient()
memory_graph = KnowledgeGraph()
trigger_client = TriggerClient()
speech_client = SpeechmaticsClient()
command_parser = CommandParser()

engine = AutoFocusEngine(
    bright_data=bright_data,
    memory_graph=memory_graph,
    trigger_client=trigger_client,
    ws_broadcaster=broadcast,
)


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NexusIntel AI starting up...")
    await memory_graph.initialize()
    if not config.DEMO_MODE:
        engine.start()
    else:
        logger.info("DEMO_MODE=true — Auto-Focus Engine paused (use /engine/demo to trigger insights)")
    yield
    logger.info("NexusIntel AI shutting down...")
    await engine.stop()


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="NexusIntel AI",
    description="Unified Autonomous Deep-Web Intelligence Matrix",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(engine_router, prefix="/api")
app.include_router(gtm_router, prefix="/api")
app.include_router(finance_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.include_router(voice_router, prefix="/api")


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "NexusIntel AI",
        "version": "1.0.0",
        "status": "running",
        "tracks": ["gtm", "finance", "security"],
        "engine": engine.get_status(),
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
