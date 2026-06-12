"""
crop_category.py
SQLAlchemy ORM model for the crop_categories table.

This module defines the CropCategory lookup entity used
to classify crops into predefined categories.
"""

from sqlalchemy import (
    BigInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.mixins import TimestampMixin
from app.models.crop import Crop


class CropCategory(TimestampMixin, Base):
    """ORM model for the crop_categories table."""

    __tablename__ = "crop_categories"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    crops: Mapped[list["Crop"]] = relationship(
        back_populates="category",
    )
