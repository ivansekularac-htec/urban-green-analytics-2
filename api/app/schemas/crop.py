from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class CropBase(BaseModel):
    category_id: int
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CropCreate(CropBase):
    pass


class CropResponse(CropBase, BaseResponse):
    pass
