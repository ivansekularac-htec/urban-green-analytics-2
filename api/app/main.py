"""
main.py

Application entry point for the Urban Green Analytics API.

This module creates and configures the FastAPI application instance,
registers application lifecycle events, and defines root-level endpoints.

During application startup, a database connectivity check is performed
to verify that the API can successfully establish a connection to the
configured PostgreSQL database. This helps detect configuration or
infrastructure issues early and prevents the application from running
without database access.
"""
from contextlib import asynccontextmanager

import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("STARTUP FUNCTION EXECUTED")

    try:
        with engine.connect() as connection:
            print("CONNECTED TO ENGINE")

            connection.execute(text("SELECT 1"))

            print("QUERY EXECUTED")

    except Exception as exc:
        print(f"DATABASE ERROR: {exc}")
        raise

    yield

app = FastAPI(
    title="Urban Green Analytics API",
    description="Backend API for the Urban Green Analytics platform.",
    version="0.1.0",
     lifespan=lifespan,
)

@app.get("/")
def root() -> dict[str, str]:
    """
    Return a basic API status message.

    This endpoint serves as a lightweight health check that can be used
    to verify that the FastAPI application is running and able to accept
    HTTP requests.

    Returns:
        dict[str, str]:
            A simple response containing the current API status message.
    """
    return {"message": "Urban Green API is running"}
