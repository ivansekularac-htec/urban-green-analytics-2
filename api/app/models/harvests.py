from decimal import Decimal
from sqlalchemy import BigInteger, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.helpers import get_current_timestamp


class Harvest(Base):
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

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
        onupdate=get_current_timestamp,
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