"""
crop.py
Crop and crop category models.
"""

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class CropCategory(Base, TimestampMixin):
    """Model for crop categories."""

    __tablename__ = "crop_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    crops: Mapped[list["Crop"]] = relationship("Crop", back_populates="category")


class Crop(Base, TimestampMixin):
    """Model for crops."""

    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("crop_categories.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500))
    category: Mapped["CropCategory"] = relationship("CropCategory", back_populates="crops")
    farm_crops: Mapped[list["FarmCrop"]] = relationship("FarmCrop", back_populates="crop")
    harvests: Mapped[list["Harvest"]] = relationship("Harvest", back_populates="crop")
