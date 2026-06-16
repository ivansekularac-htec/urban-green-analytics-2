from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.quality_grade import QualityGradeCreate


def create(
    db: Session,
    payload: QualityGradeCreate,
) -> QualityGrade:

    obj = QualityGrade(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    quality_grade_id: int,
) -> QualityGrade | None:

    return db.get(QualityGrade, quality_grade_id)


def get_all(
    db: Session,
) -> list[QualityGrade]:

    return list(db.scalars(select(QualityGrade)).all())
