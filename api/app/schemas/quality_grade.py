from pydantic import BaseModel, ConfigDict, Field


class QualityGradeBase(BaseModel):
    """Base schema for quality grade data."""

    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: str | None = Field(max_length=500)


class QualityGradeCreate(QualityGradeBase):
    """Schema for creating a quality grade."""

    pass


class QualityGradeUpdate(BaseModel):
    """Schema for updating quality grade data."""

    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class QualityGradeResponse(QualityGradeBase):
    """Schema for returning quality grade data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
