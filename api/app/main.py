"""
main.py
Application entry point for the Urban Green Analytics API.

This module creates the FastAPI application instance and defines the
root health-check endpoint.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import verify_database_connection
from app.routers.crops.crop import crop_router
from app.routers.crops.crop_category import crop_category_router
from app.routers.crops.farm_crop import farm_crop_router
from app.routers.farms.farms import farm_router
from app.routers.farms.growing_system_type import growing_system_type_router
from app.routers.farms.infrastructure_type import infrastructure_type_router
from app.routers.harvests.harvests import harvest_router
from app.routers.harvests.quality_grade import quality_grade_router
from app.routers.sensors.sensor import sensor_router
from app.routers.sensors.sensor_type import sensor_type_router
from app.routers.users.role import role_router
from app.routers.users.user import user_router
from app.routers.users.user_roles import user_role_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_V1_PREFIX = get_settings().api_v1_prefix


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

app.include_router(router=crop_category_router, prefix=API_V1_PREFIX)
app.include_router(router=crop_router, prefix=API_V1_PREFIX)
app.include_router(router=farm_crop_router, prefix=API_V1_PREFIX)
app.include_router(router=farm_router, prefix=API_V1_PREFIX)
app.include_router(router=growing_system_type_router, prefix=API_V1_PREFIX)
app.include_router(router=infrastructure_type_router, prefix=API_V1_PREFIX)
app.include_router(router=harvest_router, prefix=API_V1_PREFIX)
app.include_router(router=quality_grade_router, prefix=API_V1_PREFIX)
app.include_router(router=sensor_type_router, prefix=API_V1_PREFIX)
app.include_router(router=sensor_router, prefix=API_V1_PREFIX)
app.include_router(router=user_router, prefix=API_V1_PREFIX)
app.include_router(router=role_router, prefix=API_V1_PREFIX)
app.include_router(router=user_role_router, prefix=API_V1_PREFIX)


@app.get("/")
def root() -> dict[str, str]:
    """Return a basic API status message.

    This endpoint can be used as a simple health check to verify that the
    application is running.

    Returns:
        dict[str, str]: A response containing the API status message.
    """
    return {"message": "Urban Green API is running"}
