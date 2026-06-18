"""
Quality grade API routes.

Reference data — readable by any authenticated user; only Admin can write.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.harvests.quality_grade import QualityGradeRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)
from app.security.dependencies import get_current_user, require_roles
from app.security.roles import RoleName
from app.services.harvests.quality_grade import QualityGradeService

router = APIRouter(
    prefix="/quality-grades",
    tags=["Quality Grades"],
    dependencies=[Depends(get_current_user)],
)


def get_quality_grade_service(db: DatabaseSession) -> QualityGradeService:
    """Create and return a QualityGrade service instance."""
    return QualityGradeService(QualityGradeRepository(db))


QualityGradeServiceDep = Annotated[
    QualityGradeService,
    Depends(get_quality_grade_service),
]


@router.get("", response_model=list[QualityGradeResponse])
def list_quality_grades(service: QualityGradeServiceDep, pagination: PaginationDep):
    """List quality grade records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{quality_grade_id}", response_model=QualityGradeResponse)
def get_quality_grade(quality_grade_id: int, service: QualityGradeServiceDep):
    """Get a quality grade record by ID."""
    return service.get(quality_grade_id)


@router.post(
    "",
    response_model=QualityGradeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def create_quality_grade(payload: QualityGradeCreate, service: QualityGradeServiceDep):
    """Create a quality grade record (Admin only)."""
    return service.create(payload)


@router.put(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def update_quality_grade(
    quality_grade_id: int,
    payload: QualityGradeUpdate,
    service: QualityGradeServiceDep,
):
    """Update a quality grade record by ID (Admin only)."""
    return service.update(quality_grade_id, payload)


@router.delete(
    "/{quality_grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def delete_quality_grade(quality_grade_id: int, service: QualityGradeServiceDep):
    """Delete a quality grade record by ID (Admin only)."""
    service.delete(quality_grade_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
