from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class SensorTypeBase(BaseModel):
    """
    Shared fields for SensorType entity.
    """

    name: str = Field(default=None, max_length=100)
    unit: str = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)

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

    name: str = Field(default=None, max_length=100)
    unit: str = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)

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
