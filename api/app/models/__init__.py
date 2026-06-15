"""
SQLAlchemy model registry.

This file ensures all ORM models are imported so that
SQLAlchemy can resolve relationships (especially string-based ones)
during mapper configuration.
"""

# -------------------------
# CROPS
# -------------------------
from app.models.crops.crop import Crop
from app.models.crops.crop_category import CropCategory
from app.models.crops.farm_crop import FarmCrop

# -------------------------
# FARMS
# -------------------------
from app.models.farms.farm import Farm
from app.models.farms.farm_status import FarmStatus
from app.models.farms.growing_system_type import GrowingSystemType
from app.models.farms.infrastructure_type import InfrastructureType

# -------------------------
# HARVESTS
# -------------------------
from app.models.harvests.harvest import Harvest
from app.models.harvests.quality_grade import QualityGrade

# -------------------------
# SENSORS
# -------------------------
from app.models.sensors.sensor import Sensor
from app.models.sensors.sensor_type import SensorType

# -------------------------
# USERS
# -------------------------
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole

__all__ = [
    # users
    "User",
    "UserRole",
    "Role",
    # farms
    "Farm",
    "FarmStatus",
    "GrowingSystemType",
    "InfrastructureType",
    # crops
    "Crop",
    "CropCategory",
    "FarmCrop",
    # sensors
    "Sensor",
    "SensorType",
    # harvests
    "Harvest",
    "QualityGrade",
]
