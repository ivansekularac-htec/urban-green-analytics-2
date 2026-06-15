"""
Pydantic schema exports.

Central import point for all API schemas to avoid
circular imports and simplify test imports.
"""

# -------------------------
# AUDIT
# -------------------------
from app.schemas.audit import AuditSchema

# -------------------------
# CROPS
# -------------------------
from app.schemas.crops.crop import (
    CropBase,
    CropCreate,
    CropResponse,
    CropUpdate,
)
from app.schemas.crops.crop_category import (
    CropCategoryBase,
    CropCategoryCreate,
    CropCategoryResponse,
)
from app.schemas.crops.farm_crop import (
    FarmCropBase,
    FarmCropCreate,
    FarmCropResponse,
)

# -------------------------
# FARMS
# -------------------------
from app.schemas.farms.farm import (
    FarmBase,
    FarmCreate,
    FarmResponse,
    FarmUpdate,
)
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeBase,
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
)
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeBase,
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
)

# -------------------------
# HARVESTS
# -------------------------
from app.schemas.harvests.harvest import (
    HarvestBase,
    HarvestCreate,
    HarvestResponse,
)
from app.schemas.harvests.quality_grade import (
    QualityGradeBase,
    QualityGradeCreate,
    QualityGradeResponse,
)

# -------------------------
# SENSORS
# -------------------------
from app.schemas.sensors.sensor import (
    SensorBase,
    SensorCreate,
    SensorResponse,
    SensorUpdate,
)
from app.schemas.sensors.sensor_type import (
    SensorTypeBase,
    SensorTypeCreate,
    SensorTypeResponse,
)
from app.schemas.users.role import (
    RoleBase,
    RoleCreate,
    RoleResponse,
)

# -------------------------
# USERS
# -------------------------
from app.schemas.users.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.schemas.users.user_roles import (
    UserRoleBase,
    UserRoleCreate,
    UserRoleResponse,
)

# -------------------------
# EXPORTS
# -------------------------
__all__ = [
    # audit
    "AuditSchema",
    # farms
    "FarmBase",
    "FarmCreate",
    "FarmUpdate",
    "FarmResponse",
    "InfrastructureTypeBase",
    "InfrastructureTypeCreate",
    "InfrastructureTypeUpdate",
    "InfrastructureTypeResponse",
    "GrowingSystemTypeBase",
    "GrowingSystemTypeCreate",
    "GrowingSystemTypeUpdate",
    "GrowingSystemTypeResponse",
    # crops
    "CropBase",
    "CropCreate",
    "CropUpdate",
    "CropResponse",
    "CropCategoryBase",
    "CropCategoryCreate",
    "CropCategoryUpdate",
    "CropCategoryResponse",
    "FarmCropBase",
    "FarmCropCreate",
    "FarmCropUpdate",
    "FarmCropResponse",
    # sensors
    "SensorBase",
    "SensorCreate",
    "SensorUpdate",
    "SensorResponse",
    "SensorTypeBase",
    "SensorTypeCreate",
    "SensorTypeUpdate",
    "SensorTypeResponse",
    # users
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "UserRoleBase",
    "UserRoleCreate",
    "UserRoleUpdate",
    "UserRoleResponse",
    # harvests
    "HarvestBase",
    "HarvestCreate",
    "HarvestUpdate",
    "HarvestResponse",
    "QualityGradeBase",
    "QualityGradeCreate",
    "QualityGradeUpdate",
    "QualityGradeResponse",
]
