"""
farm_crop.py
Farm-crop association model.
"""

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class FarmCrop(Base, TimestampMixin):
    """Model for associating crops with farms."""

    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[int] = mapped_column(BigInteger)
    ended_at: Mapped[int | None] = mapped_column(BigInteger)
    farm: Mapped["Farm"] = relationship("Farm", back_populates="farm_crops")
    crop: Mapped["Crop"] = relationship("Crop", back_populates="farm_crops")
