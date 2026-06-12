from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.enums import FarmStatus, SensorStatus

"""
Lookup Tables
"""


##########################
# Role
##########################
class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Quality Grade
##########################
class QualityGradeBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeResponse(QualityGradeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Farm Infrastructure Type
##########################
class FarmInfrastructureTypeBase(BaseModel):
    name: str
    description: str | None = None


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    pass


class FarmInfrastructureTypeResponse(FarmInfrastructureTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Growing System Type
##########################
class GrowingSystemTypeBase(BaseModel):
    name: str
    description: str | None = None


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeResponse(GrowingSystemTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Crop Category
##########################
class CropCategoryBase(BaseModel):
    name: str
    description: str | None = None


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryResponse(CropCategoryBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Sensor Type
##########################
class SensorTypeBase(BaseModel):
    name: str
    unit: str
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeResponse(SensorTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


"""
Main Tables
"""


##########################
# Farm
##########################
class FarmBase(BaseModel):
    infrastructure_type_id: int
    growing_system_type_id: int

    name: str
    city: str | None = None

    size_m2: float | None = None
    status: FarmStatus
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    pass


class FarmResponse(FarmBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# User
##########################
class UserBase(BaseModel):
    email: str
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    password_hash: str


class UserResponse(UserBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Crop
##########################
class CropBase(BaseModel):
    category_id: int
    name: str
    description: str | None = None


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Sensor
##########################
class SensorBase(BaseModel):
    farm_id: int
    sensor_type_id: int

    serial_number: str
    status: SensorStatus
    installed_at: int | None = None


class SensorCreate(SensorBase):
    pass


class SensorResponse(SensorBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Harvest
##########################
class HarvestBase(BaseModel):
    farm_id: int
    crop_id: int
    quality_grade_id: int

    weight_kg: Decimal


class HarvestCreate(HarvestBase):
    pass


class HarvestResponse(HarvestBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


"""
Many to Many Tables
"""


##########################
# User Role
##########################
class UserRoleBase(BaseModel):
    user_id: int
    role_id: int
    farm_id: int | None = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleResponse(UserRoleBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##########################
# Farm Crop
##########################
class FarmCropBase(BaseModel):
    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    pass


class FarmCropResponse(FarmCropBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
