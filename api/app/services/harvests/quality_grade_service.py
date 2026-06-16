from sqlalchemy.orm import Session

from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.quality_grade import QualityGradeCreate, QualityGradeUpdate


def create_quality_grade(db: Session, data: QualityGradeCreate) -> QualityGrade:
    quality_grade = QualityGrade(**data.model_dump())

    db.add(quality_grade)
    db.commit()
    db.refresh(quality_grade)

    return quality_grade


def get_quality_grades(db: Session) -> list[QualityGrade]:
    return db.query(QualityGrade).all()


def update_quality_grade(
    db: Session,
    quality_grade: QualityGrade,
    data: QualityGradeUpdate,
) -> QualityGrade:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(quality_grade, field, value)

    db.commit()
    db.refresh(quality_grade)

    return quality_grade


def delete_quality_grade(db: Session, quality_grade: QualityGrade) -> None:
    db.delete(quality_grade)
    db.commit()
