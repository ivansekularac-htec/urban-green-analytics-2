from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models import Crop, TimestampMixin


class CropCategory(TimestampMixin, Base):
    """ORM model representing a crop category."""

    __tablename__ = "crop_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    crops: Mapped[list[Crop]] = relationship(back_populates="category")
