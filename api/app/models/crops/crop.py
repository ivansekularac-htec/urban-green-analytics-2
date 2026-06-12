"""
Crop ORM model.

Represents a crop entity that belongs to a category and can be
cultivated on farms and tracked through harvest records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.crops.crop_category import CropCategory
    from app.models.crops.farm_crop import FarmCrop
    from app.models.harvests.harvest import Harvest


class Crop(Base, AuditMixin):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("crop_categories.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    category: Mapped[CropCategory] = relationship(
        back_populates="crops",
    )

    farm_crops: Mapped[list[FarmCrop]] = relationship(
        back_populates="crop",
    )

    harvests: Mapped[list[Harvest]] = relationship(
        back_populates="crop",
    )
