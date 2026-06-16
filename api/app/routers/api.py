"""
Central API router registration.
"""

from fastapi import APIRouter

from app.routers.crops.crop_categories import router as crop_categories_router
from app.routers.crops.crops import router as crops_router
from app.routers.crops.farm_crops import router as farm_crops_router
from app.routers.farms.farms import router as farms_router
from app.routers.farms.growing_system_types import router as growing_system_types_router
from app.routers.farms.infrastructure_types import router as infrastructure_types_router
from app.routers.harvests.harvests import router as harvests_router
from app.routers.harvests.quality_grades import router as quality_grades_router
from app.routers.sensors.sensor_types import router as sensor_types_router
from app.routers.sensors.sensors import router as sensors_router
from app.routers.users.roles import router as roles_router
from app.routers.users.user_roles import router as user_roles_router
from app.routers.users.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(farms_router)
api_router.include_router(infrastructure_types_router)
api_router.include_router(growing_system_types_router)

api_router.include_router(crops_router)
api_router.include_router(crop_categories_router)
api_router.include_router(farm_crops_router)

api_router.include_router(harvests_router)
api_router.include_router(quality_grades_router)

api_router.include_router(sensors_router)
api_router.include_router(sensor_types_router)

api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(user_roles_router)
