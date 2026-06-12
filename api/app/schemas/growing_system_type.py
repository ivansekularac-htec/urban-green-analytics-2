from pydantic import BaseModel, ConfigDict


class GrowingSystemTypeBase(BaseModel):
    """Base schema for growing system type data."""

    name: str
    description: str | None = None


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    """Schema for creating a growing system type."""

    pass


class GrowingSystemTypeResponse(GrowingSystemTypeBase):
    """Schema for returning growing system type data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
