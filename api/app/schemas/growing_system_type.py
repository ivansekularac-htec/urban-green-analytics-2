from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class GrowingSystemTypeBase(BaseModel):
    """Base schema for growing system types."""

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    """Schema used for growing system type creation."""

    pass


class GrowingSystemTypeUpdate(BaseModel):
    """Schema used for partial growing system type updates."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class GrowingSystemTypeResponse(GrowingSystemTypeBase, TimestampResponse):
    """Schema returned when retrieving growing system type information."""

    pass
