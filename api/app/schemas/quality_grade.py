from pydantic import BaseModel, ConfigDict


class QualityGradeBase(BaseModel):
    """Base schema for quality grade data."""

    code: str
    name: str
    description: str | None = None


class QualityGradeCreate(QualityGradeBase):
    """Schema for creating a quality grade."""

    pass


class QualityGradeResponse(QualityGradeBase):
    """Schema for returning quality grade data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
