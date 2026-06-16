from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)

quality_grades_router = APIRouter(prefix="/quality-grades", tags=["quality-grades"])


@quality_grades_router.post(
    "/",
    response_model=QualityGradeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_grade(
    payload: QualityGradeCreate,
    db: DbSession,
) -> QualityGrade:
    quality_grade = QualityGrade(**payload.model_dump())

    db.add(quality_grade)
    db.commit()
    db.refresh(quality_grade)

    return quality_grade


@quality_grades_router.get(
    "/",
    response_model=list[QualityGradeResponse],
)
def get_quality_grades(
    db: DbSession,
) -> list[QualityGrade]:
    return db.scalars(select(QualityGrade)).all()


@quality_grades_router.get(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
)
def get_quality_grade(
    quality_grade_id: int,
    db: DbSession,
) -> QualityGrade:
    quality_grade = db.scalar(select(QualityGrade).where(QualityGrade.id == quality_grade_id))

    if quality_grade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality grade not found",
        )

    return quality_grade


@quality_grades_router.put(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
)
def update_quality_grade(
    quality_grade_id: int,
    payload: QualityGradeUpdate,
    db: DbSession,
) -> QualityGrade:
    quality_grade = db.scalar(select(QualityGrade).where(QualityGrade.id == quality_grade_id))

    if quality_grade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality grade not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(quality_grade, field, value)

    db.commit()

    return quality_grade


@quality_grades_router.delete(
    "/{quality_grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_grade(
    quality_grade_id: int,
    db: DbSession,
) -> None:
    quality_grade = db.scalar(select(QualityGrade).where(QualityGrade.id == quality_grade_id))

    if quality_grade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality grade not found",
        )

    db.delete(quality_grade)
    db.commit()
