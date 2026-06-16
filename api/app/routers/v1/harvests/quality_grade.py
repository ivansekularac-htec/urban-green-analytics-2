from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import QualityGrade
from app.schemas import QualityGradeCreate, QualityGradeResponse, QualityGradeUpdate

quality_grade_router = APIRouter(
    prefix="/quality-grades",
    tags=["Quality Grades"],
)


@quality_grade_router.get(
    "/",
    response_model=list[QualityGradeResponse],
)
def get_quality_grades(
    db: Session = Depends(get_db),
):
    return db.query(QualityGrade).all()


@quality_grade_router.post(
    "/",
    response_model=QualityGradeResponse,
    status_code=201,
)
def create_quality_grade(
    quality_grade_data: QualityGradeCreate,
    db: Session = Depends(get_db),
):
    quality_grade = QualityGrade(
        **quality_grade_data.model_dump(),
    )

    db.add(quality_grade)
    db.commit()
    db.refresh(quality_grade)

    return quality_grade


@quality_grade_router.put(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
)
def update_quality_grade(
    quality_grade_id: int,
    quality_grade_data: QualityGradeUpdate,
    db: Session = Depends(get_db),
):
    quality_grade = db.query(QualityGrade).filter(QualityGrade.id == quality_grade_id).first()

    if quality_grade is None:
        raise HTTPException(
            status_code=404,
            detail="Quality grade not found",
        )

    for field, value in quality_grade_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(quality_grade, field, value)

    db.commit()
    db.refresh(quality_grade)

    return quality_grade
