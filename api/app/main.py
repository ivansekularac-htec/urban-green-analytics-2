"""
main.py
Application entry point for the Urban Green Analytics API.

This module creates the FastAPI application instance and defines the
root health-check endpoint.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import verify_database_connection
from app.routers.crops.crop import router as crop_router
from app.routers.crops.crop_category import router as crop_category_router
from app.routers.crops.farm_crop import router as farm_role_router
from app.routers.farms.farm import router as farms_router
from app.routers.farms.growing_system_type import router as growing_system_type_router
from app.routers.farms.infrastructure_type import router as infrastructure_type_router
from app.routers.harvests.harvest import router as harvest_router
from app.routers.harvests.quality_grade import router as quality_grade_router
from app.routers.sensors.sensor import router as sensor_router
from app.routers.sensors.sensor_type import router as sensor_type_router
from app.routers.users.role import router as role_router
from app.routers.users.user import router as user_router
from app.routers.users.user_roles import router as user_role_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.config import get_settings

settings = get_settings()


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

app.include_router(role_router, prefix=settings.api_version_v1)
app.include_router(user_router, prefix=settings.api_version_v1)
app.include_router(user_role_router, prefix=settings.api_version_v1)
app.include_router(sensor_router, prefix=settings.api_version_v1)
app.include_router(sensor_type_router, prefix=settings.api_version_v1)
app.include_router(harvest_router, prefix=settings.api_version_v1)
app.include_router(quality_grade_router, prefix=settings.api_version_v1)
app.include_router(farms_router, prefix=settings.api_version_v1)
app.include_router(growing_system_type_router, prefix=settings.api_version_v1)
app.include_router(infrastructure_type_router, prefix=settings.api_version_v1)
app.include_router(crop_router, prefix=settings.api_version_v1)
app.include_router(crop_category_router, prefix=settings.api_version_v1)
app.include_router(farm_role_router, prefix=settings.api_version_v1)


@app.get("/")
def root() -> dict[str, str]:
    """Return a basic API status message.

    This endpoint can be used as a simple health check to verify that the
    application is running.

    Returns:
        dict[str, str]: A response containing the API status message.
    """
    return {"message": "Urban Green API is running"}
