from pydantic import BaseModel, Field

from app.models.enums import SensorStatus
from app.schemas.common import TimestampResponse


class SensorBase(BaseModel):
    """Base schema for sensor data."""

    farm_id: int
    sensor_type_id: int
    serial_number: str = Field(max_length=255)
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    """Schema used for sensor creation."""

    pass


class SensorUpdate(BaseModel):
    """Schema used for partial sensor updates."""

    farm_id: int | None = None
    sensor_type_id: int | None = None
    serial_number: str | None = Field(default=None, max_length=255)
    status: SensorStatus | None = None
    installed_at: int | None = None


class SensorResponse(SensorBase, TimestampResponse):
    """Schema returned when retrieving sensor information."""

    pass
