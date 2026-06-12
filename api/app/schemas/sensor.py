from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SensorStatus


class SensorBase(BaseModel):
    farm_id: int
    sensor_type_id: int
    serial_number: str = Field(max_length=255)
    status: SensorStatus
    installed_at: int | None = None


class SensorCreate(SensorBase):
    pass


class SensorResponse(SensorBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class SensorUpdate(BaseModel):
    farm_id: int | None = None
    sensor_type_id: int | None = None
    serial_number: str | None = None
    status: SensorStatus | None = None
    installed_at: int | None = None
