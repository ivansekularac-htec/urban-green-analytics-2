"""
@File: main.py
Application entry point for the Urban Green Analytics API.

This module creates the FastAPI application instance, verifies the database
connection during application startup, and defines the root health-check
endpoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import verify_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run application startup and shutdown tasks.

    The database connection is verified before the application starts serving
    requests. If the connection fails, application startup will fail.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control is yielded back to FastAPI while the application is running.
    """
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
    """Return a basic API status message.

    This endpoint can be used as a simple health check to verify that the
    application is running.

    Returns:
        dict[str, str]: A response containing the API status message.
    """
    return {"message": "Urban Green API is running"}
