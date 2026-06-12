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


class SensorResponse(SensorBase, BaseResponse):
    pass
