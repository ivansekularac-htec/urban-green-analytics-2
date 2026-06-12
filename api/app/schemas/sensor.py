from pydantic import BaseModel, Field

from app.enums import SensorStatus
from app.schemas.base import BaseResponse


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


class SensorUpdate(BaseModel):
    farm_id: int | None = None
    sensor_type_id: int | None = None

    serial_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    status: SensorStatus | None = None
    installed_at: int | None = None


class SensorResponse(SensorBase, BaseResponse):
    pass
