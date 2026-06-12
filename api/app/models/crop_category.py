"""
crop_category.py
SQLAlchemy ORM model for the crop_categories table.

This module defines the CropCategory lookup entity used
to classify crops into predefined categories.
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.crop import Crop


class CropCategory(Base, TimestampMixin):
    """ORM model for the crop_categories table."""

    __tablename__ = "crop_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500))

    crops: Mapped[list["Crop"]] = relationship(back_populates="category")
