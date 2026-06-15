from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import TimestampMixin

if TYPE_CHECKING:
    from app.models.user_role import UserRole


class Role(TimestampMixin, Base):
    """ORM model representing an application role."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user_roles: Mapped[list[UserRole]] = relationship(back_populates="role")
