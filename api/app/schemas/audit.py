"""
Common audit fields shared across all response schemas.
"""

from pydantic import BaseModel


class AuditSchema(BaseModel):
    created_at: int
    updated_at: int
