from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import init_db
from backend.routers import automations, executions, stream, workflows

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create runtime directories
    Path(settings.screenshot_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
    await init_db()
    logger.info("Database initialised")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Browser Automation Agent",
    description="Natural-language-driven browser automation powered by GPT-4.1 + Playwright",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve screenshot images for the UI preview panel
if os.path.isdir(settings.screenshot_dir):
    app.mount("/screenshots", StaticFiles(directory=settings.screenshot_dir), name="screenshots")

app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(executions.router, prefix="/api/executions", tags=["executions"])
app.include_router(automations.router, prefix="/api/automations", tags=["automations"])
app.include_router(stream.router, prefix="/api", tags=["stream"])


@app.get("/health", tags=["meta"])
async def health_check() -> dict:
    return {"status": "healthy", "version": "1.0.0"}
