from pydantic import BaseModel, ConfigDict, Field


class CropBase(BaseModel):
    """Base schema for crop data."""

    category_id: int
    name: str = Field(max_length=255)
    description: str | None = Field(max_length=500)


class CropCreate(CropBase):
    """Schema for creating a crop."""

    pass


class CropUpdate(BaseModel):
    """Schema for updating crop data."""

    category_id: int | None = None
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class CropResponse(CropBase):
    """Schema for returning crop data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
