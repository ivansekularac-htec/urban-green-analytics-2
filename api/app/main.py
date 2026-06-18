"""
main.py
Application entry point for the Urban Green Analytics API.

This module creates the FastAPI application instance and defines the
root health-check endpoint.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.superuser import ensure_superuser
from app.database import (
    settings,
    verify_database_connection,
)
from app.routers.v1.api import v1_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run application startup and shutdown logic."""

    verify_database_connection()
    ensure_superuser()

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
