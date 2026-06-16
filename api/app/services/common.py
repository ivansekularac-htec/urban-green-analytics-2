"""
common.py
Shared service utilities.

This module contains reusable helper functions used by service
and router layers.
"""

from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


def get_or_404(
    db: Session,
    model: type[ModelType],
    entity_id: int,
    entity_name: str,
) -> ModelType:
    """Return a database entity by ID or raise a 404 error.

    Args:
        db: Active database session.
        model: SQLAlchemy ORM model class.
        entity_id: Entity identifier.
        entity_name: Human-readable entity name used in the error message.

    Raises:
        HTTPException: If the entity does not exist.

    Returns:
        ModelType: Found database entity.
    """
    entity = db.get(model, entity_id)

    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found.",
        )

    return entity
