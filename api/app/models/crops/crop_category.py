"""
Crop category ORM model.

Represents a crop classification used to organize crops into categories
such as leafy greens, microgreens or specialty crops.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.crops.crop import Crop


class CropCategory(Base, AuditMixin):
    __tablename__ = "crop_categories"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    crops: Mapped[list[Crop]] = relationship(
        back_populates="category",
    )
