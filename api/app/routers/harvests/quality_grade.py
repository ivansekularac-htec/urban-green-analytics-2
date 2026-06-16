"""
API routes for QualityGrade management.
"""

from fastapi import APIRouter, Response, status

from app.database import DbSession
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)
from app.services.harvests.quality_grade import quality_grade_service

quality_grade_router = APIRouter(
    prefix="/quality-grades",
    tags=["Quality Grades"],
)


@quality_grade_router.get(
    "",
    response_model=list[QualityGradeResponse],
)
def get_quality_grades(db: DbSession):
    """
    Retrieve all quality grades.
    """

    return quality_grade_service.get_all(db)


@quality_grade_router.get(
    "/{grade_id}",
    response_model=QualityGradeResponse,
)
def get_quality_grade(
    grade_id: int,
    db: DbSession,
):
    """
    Retrieve a quality grade by ID.
    """

    return quality_grade_service.get(db, grade_id)


@quality_grade_router.post(
    "",
    response_model=QualityGradeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_grade(
    data: QualityGradeCreate,
    db: DbSession,
):
    """
    Create a new quality grade.
    """

    return quality_grade_service.create(db, data)


@quality_grade_router.put(
    "/{grade_id}",
    response_model=QualityGradeResponse,
)
def update_quality_grade(
    grade_id: int,
    data: QualityGradeUpdate,
    db: DbSession,
):
    """
    Update an existing quality grade.
    """

    return quality_grade_service.update(
        db,
        grade_id,
        data,
    )


@quality_grade_router.delete(
    "/{grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_grade(
    grade_id: int,
    db: DbSession,
):
    """
    Delete a quality grade.
    """

    quality_grade_service.delete(db, grade_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
