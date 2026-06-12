from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CropCategory(Base):
    """Model representing a crop category."""
    
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
        nullable=True,
    )

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    crops: Mapped[list["Crop"]] = relationship(
        back_populates="category",
    )