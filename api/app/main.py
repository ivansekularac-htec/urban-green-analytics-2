"""
main.py
Application entry point for the Urban Green Analytics API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models, schemas  # noqa: F401
from app.database import verify_database_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run application startup and shutdown logic."""
    verify_database_connection()
    yield


app = FastAPI(
    title="Urban Green Analytics API",
    description="Backend API for the Urban Green Analytics platform.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Urban Green API is running"}
