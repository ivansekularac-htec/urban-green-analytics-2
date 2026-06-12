from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class FarmInfrastructureTypeBase(BaseModel):
    """Base schema for farm infrastructure types."""

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    """Schema used for infrastructure type creation."""

    pass


class FarmInfrastructureTypeUpdate(BaseModel):
    """Schema used for partial infrastructure type updates."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class FarmInfrastructureTypeResponse(FarmInfrastructureTypeBase, TimestampResponse):
    """Schema returned when retrieving infrastructure type information."""

    pass
