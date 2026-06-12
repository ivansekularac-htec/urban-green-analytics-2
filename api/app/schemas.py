from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import FarmStatus, SensorStatus


class BaseResponse(BaseModel):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


"""
Lookup Tables
"""


##########################
# Role
##########################
class RoleBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase, BaseResponse):
    pass


##########################
# Quality Grade
##########################
class QualityGradeBase(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=50,
    )
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeResponse(QualityGradeBase, BaseResponse):
    pass


##########################
# Farm Infrastructure Type
##########################
class FarmInfrastructureTypeBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    pass


class FarmInfrastructureTypeResponse(FarmInfrastructureTypeBase, BaseResponse):
    pass


##########################
# Growing System Type
##########################
class GrowingSystemTypeBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeResponse(GrowingSystemTypeBase, BaseResponse):
    pass


##########################
# Crop Category
##########################
class CropCategoryBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryResponse(CropCategoryBase, BaseResponse):
    pass


##########################
# Sensor Type
##########################
class SensorTypeBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    unit: str = Field(
        min_length=1,
        max_length=50,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeResponse(SensorTypeBase, BaseResponse):
    pass


"""
Main Tables
"""


##########################
# Farm
##########################
class FarmBase(BaseModel):
    infrastructure_type_id: int
    growing_system_type_id: int

    name: str = Field(
        min_length=1,
        max_length=255,
    )
    city: str | None = Field(
        min_length=1,
        max_length=255,
    )

    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    pass


class FarmResponse(FarmBase, BaseResponse):
    pass


##########################
# User
##########################
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(
        min_length=1,
        max_length=255,
    )
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=255,
    )


class UserResponse(UserBase, BaseResponse):
    pass


##########################
# Crop
##########################
class CropBase(BaseModel):
    category_id: int
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CropCreate(CropBase):
    pass


class CropResponse(CropBase, BaseResponse):
    pass


##########################
# Sensor
##########################
class SensorBase(BaseModel):
    farm_id: int
    sensor_type_id: int

    serial_number: str = Field(
        min_length=1,
        max_length=255,
    )
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    pass


class SensorResponse(SensorBase, BaseResponse):
    pass


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


class HarvestResponse(HarvestBase, BaseResponse):
    pass


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


class UserRoleResponse(UserRoleBase, BaseResponse):
    pass


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


class FarmCropResponse(FarmCropBase, BaseResponse):
    pass
