from pydantic import BaseModel, ConfigDict


class CropBase(BaseModel):
    category_id: int
    name: str
    description: str | None = None


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
