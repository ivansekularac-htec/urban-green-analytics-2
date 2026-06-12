from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.utils import get_current_timestamp

if TYPE_CHECKING:
    from app.models.crop import Crop
    from app.models.farm import Farm


class FarmCrop(Base):
    """ORM model representing a crop assignment to a farm."""

    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=get_current_timestamp(),
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=get_current_timestamp(),
    )

    farm: Mapped[Farm] = relationship(back_populates="farm_crops")
    crop: Mapped[Crop] = relationship(back_populates="farm_crops")
