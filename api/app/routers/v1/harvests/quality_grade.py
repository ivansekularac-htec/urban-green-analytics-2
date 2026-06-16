from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)
from app.services.common import get_or_404
from app.services.harvests import quality_grade_service

router = APIRouter(
    prefix="/quality-grades",
    tags=["Quality Grades"],
)


@router.post(
    "",
    response_model=QualityGradeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_grade(
    data: QualityGradeCreate,
    db: SessionDep,
) -> QualityGradeResponse:
    return quality_grade_service.create_quality_grade(db, data)


@router.get(
    "",
    response_model=list[QualityGradeResponse],
)
def get_quality_grades(db: SessionDep) -> list[QualityGradeResponse]:
    return quality_grade_service.get_quality_grades(db)


@router.get(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
)
def get_quality_grade(
    quality_grade_id: int,
    db: SessionDep,
) -> QualityGradeResponse:
    return get_or_404(db, QualityGrade, quality_grade_id, "Quality grade")


@router.put(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
)
def update_quality_grade(
    quality_grade_id: int,
    data: QualityGradeUpdate,
    db: SessionDep,
) -> QualityGradeResponse:
    quality_grade = get_or_404(db, QualityGrade, quality_grade_id, "Quality grade")

    return quality_grade_service.update_quality_grade(db, quality_grade, data)


@router.delete(
    "/{quality_grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_grade(
    quality_grade_id: int,
    db: SessionDep,
) -> None:
    quality_grade = get_or_404(db, QualityGrade, quality_grade_id, "Quality grade")

    quality_grade_service.delete_quality_grade(db, quality_grade)
