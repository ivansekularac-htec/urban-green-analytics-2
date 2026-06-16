from fastapi import APIRouter

from app.config import get_settings
from app.routers.v1.crops.crop import crop_router
from app.routers.v1.crops.crop_category import crop_category_router
from app.routers.v1.crops.farm_crop import farm_crop_router
from app.routers.v1.farms.farm import farm_router
from app.routers.v1.farms.growing_system_type import growing_system_type_router
from app.routers.v1.farms.infrastructure_type import infrastructure_type_router
from app.routers.v1.harvests.harvest import harvest_router
from app.routers.v1.harvests.quality_grade import quality_grade_router
from app.routers.v1.sensors.sensor import sensor_router
from app.routers.v1.sensors.sensor_type import sensor_type_router
from app.routers.v1.users.role import role_router
from app.routers.v1.users.user import user_router
from app.routers.v1.users.user_role import user_role_router

settings = get_settings()

api_v1_router = APIRouter(
    prefix=settings.api_v1_prefix,
)

api_v1_router.include_router(crop_router)
api_v1_router.include_router(role_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(user_role_router)
api_v1_router.include_router(crop_category_router)
api_v1_router.include_router(farm_crop_router)
api_v1_router.include_router(sensor_router)
api_v1_router.include_router(sensor_type_router)
api_v1_router.include_router(farm_router)
api_v1_router.include_router(growing_system_type_router)
api_v1_router.include_router(infrastructure_type_router)
api_v1_router.include_router(harvest_router)
api_v1_router.include_router(quality_grade_router)
