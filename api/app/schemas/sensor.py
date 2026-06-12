from pydantic import BaseModel, ConfigDict

from app.models.enums import SensorStatus


class SensorBase(BaseModel):
    """Base schema for sensor data."""

    farm_id: int
    sensor_type_id: int
    serial_number: str
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    """Schema for creating a sensor."""

    pass


class SensorResponse(SensorBase):
    """Schema for returning sensor data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
