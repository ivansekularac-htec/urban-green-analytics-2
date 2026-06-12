"""
harvest.py
Harvest model for tracking crop harvests.
"""

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Harvest(Base, TimestampMixin):
    """Model for tracking harvest records."""

    __tablename__ = "harvests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("farms.id"), nullable=False)
    crop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("crops.id"), nullable=False)
    quality_grade_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("quality_grades.id"), nullable=False
    )
    weight_kg: Mapped[float] = mapped_column(Numeric(10, 3))
    farm: Mapped["Farm"] = relationship("Farm", back_populates="harvests")
    crop: Mapped["Crop"] = relationship("Crop", back_populates="harvests")
    quality_grade: Mapped["QualityGrade"] = relationship("QualityGrade", back_populates="harvests")

    __table_args__ = (Index("idx_harvests_farm", "farm_id", desc("updated_at")),)
