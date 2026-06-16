from fastapi import APIRouter

from app.routers.v1.farms.farm import router as _farm_router
from app.routers.v1.crops.crop_category import router as _crop_category_router
from app.routers.v1.crops.crop import router as _crop_router
from app.routers.v1.crops.farm_crop import router as _farm_crop_router
from app.routers.v1.sensors.sensor_type import router as _sensor_type_router
from app.routers.v1.sensors.sensor import router as _sensor_router
from app.routers.v1.harvests.quality_grade import router as _quality_grade_router
from app.routers.v1.harvests.harvest import router as _harvest_router
from app.routers.v1.reference_data.infrastructure_type import router as _infrastructure_type_router
from app.routers.v1.reference_data.growing_system_type import router as _growing_system_type_router
from app.routers.v1.users.role import router as _role_router
from app.routers.v1.users.user import router as _user_router
from app.routers.v1.users.user_role import router as _user_role_router
from app.config import get_settings

settings = get_settings()

v1_router = APIRouter(prefix=settings.api_app_v1_prefix)

v1_router.include_router(_farm_router)
v1_router.include_router(_crop_category_router)
v1_router.include_router(_crop_router)
v1_router.include_router(_farm_crop_router)
v1_router.include_router(_sensor_type_router)
v1_router.include_router(_sensor_router)
v1_router.include_router(_quality_grade_router)
v1_router.include_router(_harvest_router)
v1_router.include_router(_infrastructure_type_router)
v1_router.include_router(_growing_system_type_router)
v1_router.include_router(_role_router)
v1_router.include_router(_user_router)
v1_router.include_router(_user_role_router)
