"""
api.py
API v1 router registration.

This module registers all API v1 routers.
"""

from fastapi import APIRouter

from app.config import get_settings
from app.routers.v1.crops.crop import router as crops_router
from app.routers.v1.crops.crop_category import router as crop_categories_router
from app.routers.v1.crops.farm_crop import router as farm_crops_router
from app.routers.v1.farms.farm import router as farms_router
from app.routers.v1.farms.growing_system_type import router as growing_system_types_router
from app.routers.v1.farms.infrastructure_type import router as infrastructure_types_router
from app.routers.v1.harvests.harvest import router as harvests_router
from app.routers.v1.harvests.quality_grade import router as quality_grades_router
from app.routers.v1.sensors.sensor import router as sensors_router
from app.routers.v1.sensors.sensor_type import router as sensor_types_router
from app.routers.v1.users.role import router as roles_router
from app.routers.v1.users.user import router as users_router
from app.routers.v1.users.user_roles import router as user_roles_router

settings = get_settings()

api_v1_router = APIRouter(
    prefix=settings.api_app_v1_prefix,
)

api_v1_router.include_router(crop_categories_router)
api_v1_router.include_router(crops_router)
api_v1_router.include_router(farm_crops_router)
api_v1_router.include_router(farms_router)
api_v1_router.include_router(infrastructure_types_router)
api_v1_router.include_router(growing_system_types_router)
api_v1_router.include_router(harvests_router)
api_v1_router.include_router(quality_grades_router)
api_v1_router.include_router(sensors_router)
api_v1_router.include_router(sensor_types_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(roles_router)
api_v1_router.include_router(user_roles_router)
