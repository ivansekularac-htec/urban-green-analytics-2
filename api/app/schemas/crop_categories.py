from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class CropCategoryBase(BaseModel):
    name: str
    description: str | None = None


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryResponse(
    AuditModelBase,
    CropCategoryBase,
):
    pass