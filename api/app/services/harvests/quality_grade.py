from sqlalchemy.orm import Session

from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.quality_grade import QualityGradeCreate, QualityGradeUpdate


def get_quality_grades(db: Session) -> list[QualityGrade]:
    """Query and return all quality grades from the database."""
    return db.query(QualityGrade).all()


def get_quality_grade(db: Session, quality_grade_id: int) -> QualityGrade | None:
    """Return a single quality grade by ID, or None if not found."""
    return db.query(QualityGrade).filter(QualityGrade.id == quality_grade_id).first()


def create_quality_grade(db: Session, payload: QualityGradeCreate) -> QualityGrade:
    """Persist a new quality grade to the database and return it."""
    quality_grade = QualityGrade(**payload.model_dump())
    db.add(quality_grade)
    db.commit()
    db.refresh(quality_grade)
    return quality_grade


def update_quality_grade(
    db: Session, quality_grade: QualityGrade, payload: QualityGradeUpdate
) -> QualityGrade:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(quality_grade, field, value)
    db.commit()
    db.refresh(quality_grade)
    return quality_grade


def delete_quality_grade(db: Session, quality_grade: QualityGrade) -> None:
    """Delete a quality grade from the database."""
    db.delete(quality_grade)
    db.com
