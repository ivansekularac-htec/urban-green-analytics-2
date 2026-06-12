"""
schemas.__init__
Import all schemas for easy access from the schemas module.
"""

from app.schemas.base import AuditModelBase
from app.schemas.crop import (
    CropBase,
    CropCategoryBase,
    CropCategoryCreate,
    CropCategoryResponse,
    CropCategoryUpdate,
    CropCreate,
    CropResponse,
    CropUpdate,
)
from app.schemas.farm import FarmBase, FarmCreate, FarmResponse, FarmUpdate
from app.schemas.farm_crop import (
    FarmCropBase,
    FarmCropCreate,
    FarmCropResponse,
    FarmCropUpdate,
)
from app.schemas.harvest import (
    HarvestBase,
    HarvestCreate,
    HarvestResponse,
    HarvestUpdate,
)
from app.schemas.infrastructure import (
    FarmInfrastructureTypeBase,
    FarmInfrastructureTypeCreate,
    FarmInfrastructureTypeResponse,
    FarmInfrastructureTypeUpdate,
    GrowingSystemTypeBase,
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)
from app.schemas.quality_grade import (
    QualityGradeBase,
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.schemas.sensor import (
    SensorBase,
    SensorCreate,
    SensorResponse,
    SensorTypeBase,
    SensorTypeCreate,
    SensorTypeResponse,
    SensorTypeUpdate,
    SensorUpdate,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserRoleBase,
    UserRoleCreate,
    UserRoleResponse,
    UserRoleUpdate,
    UserUpdate,
)

__all__ = [
    # Base
    "AuditModelBase",
    # Role
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    # Quality Grade
    "QualityGradeBase",
    "QualityGradeCreate",
    "QualityGradeUpdate",
    "QualityGradeResponse",
    # Infrastructure
    "FarmInfrastructureTypeBase",
    "FarmInfrastructureTypeCreate",
    "FarmInfrastructureTypeUpdate",
    "FarmInfrastructureTypeResponse",
    "GrowingSystemTypeBase",
    "GrowingSystemTypeCreate",
    "GrowingSystemTypeUpdate",
    "GrowingSystemTypeResponse",
    # Crop
    "CropCategoryBase",
    "CropCategoryCreate",
    "CropCategoryUpdate",
    "CropCategoryResponse",
    "CropBase",
    "CropCreate",
    "CropUpdate",
    "CropResponse",
    # Sensor
    "SensorTypeBase",
    "SensorTypeCreate",
    "SensorTypeUpdate",
    "SensorTypeResponse",
    "SensorBase",
    "SensorCreate",
    "SensorUpdate",
    "SensorResponse",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserRoleBase",
    "UserRoleCreate",
    "UserRoleUpdate",
    "UserRoleResponse",
    # Farm
    "FarmBase",
    "FarmCreate",
    "FarmUpdate",
    "FarmResponse",
    # Farm Crop
    "FarmCropBase",
    "FarmCropCreate",
    "FarmCropUpdate",
    "FarmCropResponse",
    # Harvest
    "HarvestBase",
    "HarvestCreate",
    "HarvestUpdate",
    "HarvestResponse",
]
