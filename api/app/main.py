"""FastAPI entry point for the research management UI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from typing import Optional

from app.config import get_settings
from app.routers import dashboard, dicom, etl, export, health, imports, mosaiq, outcomes, patients, rt, statistics, xvi


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""

    settings = get_settings()
    application = FastAPI(
        title="Radiotherapy Research Data Warehouse API",
        version="0.2.0",
        description="Read-only API for de-identified radiotherapy research data.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (
        health.router,
        dashboard.router,
        patients.router,
        dicom.router,
        xvi.router,
        rt.router,
        statistics.router,
        export.router,
        mosaiq.router,
        outcomes.router,
        imports.router,
        etl.router,
    ):
        application.include_router(router, prefix="/api/v1")
    web_dir = _legacy_web_dir()
    if web_dir is not None:
        application.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
    return application


def _legacy_web_dir() -> Optional[Path]:
    legacy_home = os.getenv("RT_RESEARCH_HOME")
    if not legacy_home:
        return None
    candidate = Path(legacy_home) / "web"
    if candidate.exists():
        return candidate
    return None


app = create_app()
