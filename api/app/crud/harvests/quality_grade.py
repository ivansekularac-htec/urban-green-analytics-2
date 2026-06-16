"""
CRUD operations for quality grades.

This module provides functions for creating and retrieving
quality grade records from the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.quality_grade import QualityGradeCreate


def create(
    db: Session,
    payload: QualityGradeCreate,
) -> QualityGrade:
    """
    Create a new quality grade.

    Args:
        db: Active database session.
        payload: Quality grade data used to create the record.

    Returns:
        The newly created quality grade instance.
    """

    obj = QualityGrade(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    quality_grade_id: int,
) -> QualityGrade | None:
    """
    Retrieve a quality grade by its ID.

    Args:
        db: Active database session.
        quality_grade_id: Unique identifier of the quality grade.

    Returns:
        The quality grade instance if found, otherwise None.
    """

    return db.get(QualityGrade, quality_grade_id)


def get_all(
    db: Session,
) -> list[QualityGrade]:
    """
    Retrieve all quality grades.

    Args:
        db: Active database session.

    Returns:
        A list of all quality grade records.
    """

    return list(db.scalars(select(QualityGrade)).all())
