from pydantic import BaseModel

from app.models.sensors.sensor_status import SensorStatus
from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class SensorBase(BaseModel):
    """
    Shared fields for Sensor entity.
    """

    farm_id: int
    sensor_type_id: int

    serial_number: str

    status: SensorStatus

    installed_at: int | None = None


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class SensorCreate(SensorBase):
    """
    Schema used for creating Sensor.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class SensorUpdate(BaseModel):
    """
    Schema used for updating Sensor.
    """

    farm_id: int | None = None
    sensor_type_id: int | None = None

    serial_number: str | None = None

    status: SensorStatus | None = None

    installed_at: int | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class SensorResponse(SensorBase, AuditSchema):
    """
    API response schema for Sensor entity.
    """

    id: int

    class Config:
        from_attributes = True
