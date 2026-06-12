from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.crop import Crop
    from app.models.farm import Farm
    from app.models.quality_grade import QualityGrade


class Harvest(Base, TimestampMixin):
    """Model representing a harvest record."""

    __tablename__ = "harvests"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id"),
        nullable=False,
    )

    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id"),
        nullable=False,
    )

    quality_grade_id: Mapped[int] = mapped_column(
        ForeignKey("quality_grades.id"),
        nullable=False,
    )

    weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    farm: Mapped["Farm"] = relationship(
        back_populates="harvests",
    )

    crop: Mapped["Crop"] = relationship(
        back_populates="harvests",
    )

    quality_grade: Mapped["QualityGrade"] = relationship(
        back_populates="harvests",
    )
