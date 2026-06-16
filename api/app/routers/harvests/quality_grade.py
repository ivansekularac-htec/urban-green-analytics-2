from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.harvests import quality_grade as quality_grade_crud
from app.database import get_db
from app.schemas.harvests.quality_grade import QualityGradeCreate, QualityGradeResponse

router = APIRouter(prefix="/v1/quality_grade", tags=["Quality Grade"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=QualityGradeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_grade(
    payload: QualityGradeCreate,
    db: DBSession,
) -> QualityGradeResponse:
    return quality_grade_crud.create(db, payload)


@router.get(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
)
def get_quality_grade(
    quality_grade_id: int,
    db: DBSession,
) -> QualityGradeResponse:
    quality_grade = quality_grade_crud.get(db, quality_grade_id)

    if quality_grade is None:
        raise HTTPException(
            status_code=404,
            detail="Quality Grade not found",
        )

    return quality_grade


@router.get(
    "/",
    response_model=list[QualityGradeResponse],
)
def get_quality_grades(
    db: DBSession,
) -> list[QualityGradeResponse]:
    return quality_grade_crud.get_all(db)
