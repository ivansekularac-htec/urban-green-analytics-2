from pydantic import BaseModel, ConfigDict


class CropBase(BaseModel):
    """Base schema for crop data."""

    category_id: int
    name: str
    description: str | None = None


class CropCreate(CropBase):
    """Schema for creating a crop."""

    pass


class CropResponse(CropBase):
    """Schema for returning crop data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
