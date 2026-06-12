from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class QualityGradeBase(BaseModel):
    """Base schema for quality grade data."""

    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class QualityGradeCreate(QualityGradeBase):
    """Schema used for quality grade creation."""

    pass


class QualityGradeUpdate(BaseModel):
    """Schema used for partial quality grade updates."""

    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class QualityGradeResponse(QualityGradeBase, TimestampResponse):
    """Schema returned when retrieving quality grade information."""

    pass
