from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class CropBase(BaseModel):
    category_id: int
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=500)


class CropCreate(CropBase):
    pass


class CropUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    description: str | None = None


class CropResponse(
    AuditModelBase,
    CropBase,
):
    pass
