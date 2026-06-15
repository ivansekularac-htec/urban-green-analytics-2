from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SensorStatus


class SensorBase(BaseModel):
    """Base schema for sensor data."""

    farm_id: int
    sensor_type_id: int
    serial_number: str = Field(max_length=255)
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    """Schema for creating a sensor."""

    pass


class SensorUpdate(BaseModel):
    """Schema for updating sensor data."""

    farm_id: int | None = None
    sensor_type_id: int | None = None
    serial_number: str | None = Field(default=None, max_length=255)
    status: SensorStatus | None = None
    installed_at: int | None = None


class SensorResponse(SensorBase):
    """Schema for returning sensor data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
