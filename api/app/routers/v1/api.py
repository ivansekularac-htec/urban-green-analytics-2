"""
Central API router registration.
"""

from fastapi import APIRouter

from app.routers.v1.auth.auth import router as auth_router
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
from app.routers.v1.users.user_role import router as user_roles_router

v1_router = APIRouter()
v1_router.include_router(auth_router)
v1_router.include_router(farms_router)
v1_router.include_router(infrastructure_types_router)
v1_router.include_router(growing_system_types_router)

v1_router.include_router(crops_router)
v1_router.include_router(crop_categories_router)
v1_router.include_router(farm_crops_router)

v1_router.include_router(harvests_router)
v1_router.include_router(quality_grades_router)

v1_router.include_router(sensors_router)
v1_router.include_router(sensor_types_router)

v1_router.include_router(users_router)
v1_router.include_router(roles_router)
v1_router.include_router(user_roles_router)
