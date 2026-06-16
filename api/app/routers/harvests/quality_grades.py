"""
Quality grade API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.harvests.quality_grade_repository import QualityGradeRepository
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)
from app.services.harvests.quality_grade_service import QualityGradeService

router = APIRouter(prefix="/quality-grades", tags=["Quality Grades"])


def get_quality_grade_service(db: DatabaseSession) -> QualityGradeService:
    """Create and return a QualityGrade service instance."""
    return QualityGradeService(QualityGradeRepository(db))


QualityGradeServiceDep = Annotated[
    QualityGradeService,
    Depends(get_quality_grade_service),
]


@router.get("", response_model=list[QualityGradeResponse])
def list_quality_grades(
    service: QualityGradeServiceDep,
    skip: int = 0,
    limit: int = 100,
):
    """List quality grade records."""
    return service.list(skip=skip, limit=limit)


@router.get("/{quality_grade_id}", response_model=QualityGradeResponse)
def get_quality_grade(quality_grade_id: int, service: QualityGradeServiceDep):
    """Get a quality grade record by ID."""
    return service.get(quality_grade_id)


@router.post("", response_model=QualityGradeResponse, status_code=status.HTTP_201_CREATED)
def create_quality_grade(payload: QualityGradeCreate, service: QualityGradeServiceDep):
    """Create a quality grade record."""
    return service.create(payload)


@router.put("/{quality_grade_id}", response_model=QualityGradeResponse)
def update_quality_grade(
    quality_grade_id: int,
    payload: QualityGradeUpdate,
    service: QualityGradeServiceDep,
):
    """Update a quality grade record by ID."""
    return service.update(quality_grade_id, payload)


@router.delete("/{quality_grade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quality_grade(quality_grade_id: int, service: QualityGradeServiceDep):
    """Delete a quality grade record by ID."""
    service.delete(quality_grade_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
