"""
main.py
Application entry point for the Urban Green Analytics API.

This module creates the FastAPI application instance and defines the
root health-check endpoint.
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Crop

app = FastAPI(
    title="Urban Green Analytics API",
    description="Backend API for the Urban Green Analytics platform.",
    version="0.1.0",
)


@app.on_event("startup")
def startup() -> None:
    """
    Verify database connectivity when the application starts.

    Returns:
        None
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("Database connection successful")

    except Exception as error:
        print(f"Database connection failed: {error}")
        raise RuntimeError("Failed to connect to the database") from error


@app.get("/")
def root() -> dict[str, str]:
    """Return a basic API status message.

    This endpoint can be used as a simple health check to verify that the
    application is running.

    Returns:
        dict[str, str]: A response containing the API status message.
    """
    return {"message": "Urban Green API is running"}


@app.get("/crops")
def get_crops(db: Session = Depends(get_db)):
    """
    Retrieve all crops from the database.

    Returns:
        list[Crop]: A list of crop records.
    """
    return db.query(Crop).all()
