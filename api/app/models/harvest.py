from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.utils import get_current_timestamp

if TYPE_CHECKING:
    from app.models.crop import Crop
    from app.models.farm import Farm
    from app.models.quality_grade import QualityGrade


class Harvest(Base):
    """ORM model representing a recorded crop harvest."""

    __tablename__ = "harvests"
    __table_args__ = (Index("idx_harvests_farm", "farm_id", "updated_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False)
    quality_grade_id: Mapped[int] = mapped_column(
        ForeignKey("quality_grades.id"),
        nullable=False,
    )
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=get_current_timestamp(),
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=get_current_timestamp(),
    )

    farm: Mapped[Farm] = relationship(back_populates="harvests")
    crop: Mapped[Crop] = relationship(back_populates="harvests")
    quality_grade: Mapped[QualityGrade] = relationship(back_populates="harvests")
