"""
schemas/infrastructure.py
Pydantic schemas for farm infrastructure and growing system types.
"""

from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class FarmInfrastructureTypeBase(BaseModel):
    """Base schema for farm infrastructure types."""

    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    """Schema for creating a farm infrastructure type."""

    pass


class FarmInfrastructureTypeUpdate(BaseModel):
    """Schema for updating a farm infrastructure type."""

    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)


class FarmInfrastructureTypeResponse(AuditModelBase, FarmInfrastructureTypeBase):
    """Schema for farm infrastructure type response."""

    pass


class GrowingSystemTypeBase(BaseModel):
    """Base schema for growing system types."""

    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    """Schema for creating a growing system type."""

    pass


class GrowingSystemTypeUpdate(BaseModel):
    """Schema for updating a growing system type."""

    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)


class GrowingSystemTypeResponse(AuditModelBase, GrowingSystemTypeBase):
    """Schema for growing system type response."""

    pass
