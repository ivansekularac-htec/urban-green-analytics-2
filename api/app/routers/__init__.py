from fastapi import APIRouter

from app.config import get_settings
from app.routers.crops.crop import router as crop_router
from app.routers.crops.crop_category import router as crop_category_router
from app.routers.crops.farm_crop import router as farm_crop_router
from app.routers.farms.farm import router as farm_router
from app.routers.farms.growing_system_type import router as growing_system_type_router
from app.routers.farms.infrastructure_type import router as infrastructure_type_router
from app.routers.harvests.harvest import router as harvest_router
from app.routers.harvests.quality_grade import router as quality_grade_router
from app.routers.sensors.sensor import router as sensor_router
from app.routers.sensors.sensor_type import router as sensor_type_router
from app.routers.users.role import router as role_router
from app.routers.users.user import router as user_router
from app.routers.users.user_roles import router as user_role_router

settings = get_settings()

v1_router = APIRouter(prefix=settings.api_version_v1)

v1_router.include_router(farm_router)
v1_router.include_router(crop_category_router)
v1_router.include_router(crop_router)
v1_router.include_router(farm_crop_router)
v1_router.include_router(sensor_type_router)
v1_router.include_router(sensor_router)
v1_router.include_router(quality_grade_router)
v1_router.include_router(harvest_router)
v1_router.include_router(infrastructure_type_router)
v1_router.include_router(growing_system_type_router)
v1_router.include_router(role_router)
v1_router.include_router(user_router)
v1_router.include_router(user_role_router)
