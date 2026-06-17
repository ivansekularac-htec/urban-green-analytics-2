"""
Quality grade repository.
"""

from sqlalchemy.orm import Session

from app.models.harvests.quality_grade import QualityGrade
from app.repositories.base_repository import BaseRepository


class QualityGradeRepository(BaseRepository[QualityGrade]):
    """
    Repository for QualityGrade database operations.
    """

    def __init__(self, db: Session):
        super().__init__(QualityGrade, db)
