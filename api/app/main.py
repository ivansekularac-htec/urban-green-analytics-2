"""
main.py
Application entry point for the Urban Green Analytics API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import SessionLocal, verify_database_connection
from app.routers.v1.api import v1_router
from app.services.auth.bootstrap import ensure_superuser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run application startup and shutdown logic.
    """

    verify_database_connection()

    db = SessionLocal()

    try:
        ensure_superuser(
            db=db,
            email=settings.api_app_superuser_username,
            password=settings.api_app_superuser_password,
        )
    finally:
        db.close()

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
    """
    Return a basic API status message.

    Returns:
        dict[str, str]: A response containing the API status message.
    """
    return {"message": "Urban Green API is running"}
