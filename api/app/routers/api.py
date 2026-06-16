from fastapi import APIRouter

from app.routers.v1.crops import crop_categories_router, crops_router, farm_crops_router
from app.routers.v1.farms import (
    farms_router,
    growing_system_types_router,
    infrastructure_types_router,
)
from app.routers.v1.harvests.harvests import harvests_router
from app.routers.v1.health import health_router
from app.routers.v1.sensors.sensor_types import sensor_types_router
from app.routers.v1.sensors.sensors import sensors_router
from app.routers.v1.users import roles_router, user_roles_router, users_router

v1_router = APIRouter(prefix="/api/v1")


v1_router.include_router(farms_router)
v1_router.include_router(infrastructure_types_router)
v1_router.include_router(growing_system_types_router)
v1_router.include_router(crops_router)
v1_router.include_router(crop_categories_router)
v1_router.include_router(farm_crops_router)
v1_router.include_router(harvests_router)
v1_router.include_router(sensor_types_router)
v1_router.include_router(sensors_router)
v1_router.include_router(roles_router)
v1_router.include_router(user_roles_router)
v1_router.include_router(users_router)
v1_router.include_router(health_router)
