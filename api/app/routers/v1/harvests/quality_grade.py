from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)
from app.services.harvests import quality_grade as quality_grade_service

router = APIRouter(prefix="/quality-grades", tags=["quality-grades"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[QualityGradeResponse])
def get_quality_grades(db: DbSession):
    """List all quality grades."""
    return quality_grade_service.get_quality_grades(db)


@router.get("/{quality_grade_id}", response_model=QualityGradeResponse)
def get_quality_grade(quality_grade_id: int, db: DbSession):
    """Retrieve a single quality grade by ID."""
    quality_grade = quality_grade_service.get_quality_grade(db, quality_grade_id)
    if not quality_grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality grade not found")
    return quality_grade


@router.post("/", response_model=QualityGradeResponse, status_code=status.HTTP_201_CREATED)
def create_quality_grade(payload: QualityGradeCreate, db: DbSession):
    """Create a new quality grade."""
    return quality_grade_service.create_quality_grade(db, payload)


@router.put("/{quality_grade_id}", response_model=QualityGradeResponse)
def update_quality_grade(quality_grade_id: int, payload: QualityGradeUpdate, db: DbSession):
    """Update an existing quality grade."""
    quality_grade = quality_grade_service.get_quality_grade(db, quality_grade_id)
    if not quality_grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality grade not found")
    return quality_grade_service.update_quality_grade(db, quality_grade, payload)


@router.delete("/{quality_grade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quality_grade(quality_grade_id: int, db: DbSession):
    """Delete a quality grade."""
    quality_grade = quality_grade_service.get_quality_grade(db, quality_grade_id)
    if not quality_grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality grade not found")
    quality_grade_service.delete_quality_grade(db, quality_grade)
