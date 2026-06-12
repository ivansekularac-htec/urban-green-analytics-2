"""
crop.py
SQLAlchemy ORM model for the crops table.

This module defines the Crop entity and its relationship
to crop categories, harvests, and farm crop assignments.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.crop_category import CropCategory
    from app.models.farm_crop import FarmCrop
    from app.models.harvest import Harvest


class Crop(TimestampMixin, Base):
    """ORM model for the crops table."""

    __tablename__ = "crops"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    category_id: Mapped[int] = mapped_column(ForeignKey("app.crop_categories.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category: Mapped["CropCategory"] = relationship(
        back_populates="crops",
    )

    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="crop",
    )

    farm_crops: Mapped[list["FarmCrop"]] = relationship(
        back_populates="crop",
    )
