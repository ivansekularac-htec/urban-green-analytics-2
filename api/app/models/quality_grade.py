"""
quality_grade.py
Quality grade model for harvest classification.
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class QualityGrade(Base, TimestampMixin):
    """Quality grade model for classifying harvested crops."""

    __tablename__ = "quality_grades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))
    harvests: Mapped[list["Harvest"]] = relationship("Harvest", back_populates="quality_grade")
