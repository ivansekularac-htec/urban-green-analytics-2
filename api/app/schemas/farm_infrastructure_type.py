from pydantic import BaseModel, ConfigDict


class FarmInfrastructureTypeBase(BaseModel):
    """Base schema for farm infrastructure type data."""

    name: str
    description: str | None = None


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    """Schema for creating a farm infrastructure type."""

    pass


class FarmInfrastructureTypeResponse(FarmInfrastructureTypeBase):
    """Schema for returning farm infrastructure type data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
