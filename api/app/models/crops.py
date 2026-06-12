from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.helpers import get_current_timestamp
    
class Crop(Base):
    """Model representing a crop."""

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
        nullable=True,
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

    category: Mapped["CropCategory"] = relationship(
        back_populates="crops",
    )

    farm_crops: Mapped[list["FarmCrop"]] = relationship(
        back_populates="crop",
    )

    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="crop",
    )