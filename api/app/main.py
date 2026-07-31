"""
main.py
Application entry point for the Urban Green Analytics API.

This module creates the FastAPI application instance and defines the
root health-check endpoint.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import SessionLocal, settings, verify_database_connection
from app.routers.v1.api import v1_router
from app.security.users import ensure_farm_manager, ensure_operations_user, ensure_superuser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run application startup and shutdown logic."""

    verify_database_connection()

    with SessionLocal() as db:
        ensure_superuser(db, settings)

        try:
            ensure_operations_user(db, settings)
        except Exception:
            logger.exception("Skipping demo Operations user bootstrap.")

        try:
            ensure_farm_manager(db, settings)
        except Exception:
            logger.exception("Skipping demo Farm Manager bootstrap.")

    yield


app = FastAPI(
    title="Urban Green Analytics API",
    description="Backend API for the Urban Green Analytics platform.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    """Return a basic API status message.

    This endpoint can be used as a simple health check to verify that the
    application is running.

    Returns:
        dict[str, str]: A response containing the API status message.
    """
    return {"message": "Urban Green API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    """Return a health status used by container orchestration probes."""
    return {"status": "ok"}
