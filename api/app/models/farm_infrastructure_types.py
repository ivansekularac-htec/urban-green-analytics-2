from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.helpers import get_current_timestamp


class FarmInfrastructureType(Base):
    """Model representing types of farm infrastructure."""
    
    __tablename__ = "farm_infrastructure_types"

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
        default=get_current_timestamp,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
        onupdate=get_current_timestamp,
    )

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="infrastructure_type",
    )