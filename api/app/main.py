"""
main.py
Application entry point for the Urban Green Analytics API.

This module creates the FastAPI application instance and defines the
root health-check endpoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import verify_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_db_connection()
    yield


app = FastAPI(
    title="Urban Green Analytics API",
    description="Backend API for the Urban Green Analytics platform.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    """Return a basic API status message.

    This endpoint can be used as a simple health check to verify that the
    application is running.

    Returns:
        dict[str, str]: A response containing the API status message.
    """
    return {"message": "Urban Green API is running"}
