from pydantic import BaseModel

from app.models.enums import SensorStatus
from app.schemas.base import AuditModelBase


class SensorBase(BaseModel):
    farm_id: int
    sensor_type_id: int
    serial_number: str
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    pass


class SensorResponse(
    AuditModelBase,
    SensorBase,
):
    pass