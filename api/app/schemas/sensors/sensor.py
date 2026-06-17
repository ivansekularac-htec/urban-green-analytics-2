from pydantic import BaseModel, ConfigDict, Field

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

    serial_number: str = Field(max_length=255)
    status: SensorStatus = SensorStatus.ACTIVE
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
# Response
# ------------------------------------------------------


class SensorResponse(SensorBase, AuditSchema):
    """
    API response schema for Sensor entity.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
