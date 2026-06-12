"""
harvest.py
SQLAlchemy ORM model for the harvests table.

This module defines the Harvest entity used to track
crop harvest records, quality grades, and yield quantities.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TIMESTAMP_DEFAULT

if TYPE_CHECKING:
    from app.models.crop import Crop
    from app.models.farm import Farm
    from app.models.quality_grade import QualityGrade


class Harvest(Base):
    """ORM model for the harvests table."""

    __tablename__ = "harvests"

    __table_args__ = (Index("idx_harvests_farm", "farm_id", "updated_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("farms.id"),
        nullable=False,
    )
    crop_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("crops.id"),
        nullable=False,
    )
    quality_grade_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quality_grades.id"),
        nullable=False,
    )
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
    )

    farm: Mapped["Farm"] = relationship(back_populates="harvests")
    crop: Mapped["Crop"] = relationship(back_populates="harvests")
    quality_grade: Mapped["QualityGrade"] = relationship(back_populates="harvests")
