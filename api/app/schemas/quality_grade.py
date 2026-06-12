from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class QualityGradeBase(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=50,
    )
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeUpdate(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class QualityGradeResponse(QualityGradeBase, BaseResponse):
    pass
