from pydantic import BaseModel, ConfigDict

from app.models.enums import SensorStatus


class SensorBase(BaseModel):
    farm_id: int
    sensor_type_id: int
    serial_number: str
    status: SensorStatus
    status: str
    installed_at: int | None = None


class SensorCreate(SensorBase):
    pass


class SensorResponse(SensorBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
