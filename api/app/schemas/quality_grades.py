from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class QualityGradeBase(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class QualityGradeResponse(AuditModelBase, QualityGradeBase):
    pass
