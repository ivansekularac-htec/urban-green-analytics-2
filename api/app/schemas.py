from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import FarmStatus, SensorStatus


class AuditModelBase(BaseModel):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleResponse(AuditModelBase, RoleBase):
    pass


class QualityGradeBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeResponse(AuditModelBase, QualityGradeBase):
    pass


class FarmInfrastructureTypeBase(BaseModel):
    name: str
    description: str | None = None


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    pass


class FarmInfrastructureTypeResponse(AuditModelBase, FarmInfrastructureTypeBase):
    pass


class GrowingSystemTypeBase(BaseModel):
    name: str
    description: str | None = None


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeResponse(AuditModelBase, GrowingSystemTypeBase):
    pass


class CropCategoryBase(BaseModel):
    name: str
    description: str | None = None


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryResponse(AuditModelBase, CropCategoryBase):
    pass


class SensorTypeBase(BaseModel):
    name: str
    unit: str
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeResponse(AuditModelBase, SensorTypeBase):
    pass


class FarmBase(BaseModel):
    infrastructure_type_id: int
    growing_system_type_id: int
    name: str
    city: str | None = None
    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    pass


class FarmResponse(AuditModelBase, FarmBase):
    pass


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(AuditModelBase, UserBase):
    pass


class CropBase(BaseModel):
    category_id: int
    name: str
    description: str | None = None


class CropCreate(CropBase):
    pass


class CropResponse(AuditModelBase, CropBase):
    pass


class UserRoleBase(BaseModel):
    user_id: int
    role_id: int
    farm_id: int | None = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleResponse(AuditModelBase, UserRoleBase):
    pass


class FarmCropBase(BaseModel):
    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    pass


class FarmCropResponse(AuditModelBase, FarmCropBase):
    pass


class SensorBase(BaseModel):
    farm_id: int
    sensor_type_id: int
    serial_number: str
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    pass


class SensorResponse(AuditModelBase, SensorBase):
    pass


class HarvestBase(BaseModel):
    farm_id: int
    crop_id: int
    quality_grade_id: int
    weight_kg: Decimal


class HarvestCreate(HarvestBase):
    pass


class HarvestResponse(AuditModelBase, HarvestBase):
    pass
