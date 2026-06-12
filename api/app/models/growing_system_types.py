from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.farm import Farm


class GrowingSystemType(Base, TimestampMixin):
    """Model representing a type of growing system used in farming operations."""

    __tablename__ = "growing_system_types"

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

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="growing_system_type",
    )
