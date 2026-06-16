"""
Quality grade service.
"""

from app.models.harvests.quality_grade import QualityGrade
from app.repositories.harvests.quality_grade_repository import QualityGradeRepository
from app.schemas.harvests.quality_grade import QualityGradeCreate, QualityGradeUpdate
from app.services.base_service import BaseService


class QualityGradeService(BaseService[QualityGrade, QualityGradeCreate, QualityGradeUpdate]):
    """
    Service for QualityGrade business logic.
    """

    def __init__(self, repository: QualityGradeRepository):
        super().__init__(repository, "Quality grade")
