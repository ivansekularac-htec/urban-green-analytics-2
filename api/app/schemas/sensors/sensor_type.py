from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class SensorTypeBase(BaseModel):
    """
    Shared fields for SensorType entity.
    """

    name: str
    unit: str

    description: str | None = None

    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class SensorTypeCreate(SensorTypeBase):
    """
    Schema used for creating SensorType.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class SensorTypeUpdate(BaseModel):
    """
    Schema used for updating SensorType.
    """

    name: str | None = None
    unit: str | None = None

    description: str | None = None

    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class SensorTypeResponse(SensorTypeBase, AuditSchema):
    """
    API response schema for SensorType.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
