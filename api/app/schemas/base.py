"""
schemas/base.py
Base Pydantic models shared across all schemas.
"""

from pydantic import BaseModel, ConfigDict


class AuditModelBase(BaseModel):
    """Base model for all responses with audit fields."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
