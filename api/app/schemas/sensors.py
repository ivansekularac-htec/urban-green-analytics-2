from pydantic import BaseModel, Field

from app.models.enums import SensorStatus
from app.schemas.base import AuditModelBase


class SensorBase(BaseModel):
    farm_id: int
    sensor_type_id: int
    serial_number: str = Field(max_length=255)
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    farm_id: int | None = None
    sensor_type_id: int | None = None
    serial_number: str | None = None
    status: SensorStatus | None = None
    installed_at: int | None = None


class SensorResponse(
    AuditModelBase,
    SensorBase,
):
    pass
