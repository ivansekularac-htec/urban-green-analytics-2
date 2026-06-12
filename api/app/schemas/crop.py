from pydantic import BaseModel, ConfigDict, Field


class CropBase(BaseModel):
    category_id: int
    name: str = Field(max_length=100)
    description: str | None = None


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class CropUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    description: str | None = None
