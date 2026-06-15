from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import TimestampMixin

if TYPE_CHECKING:
    from app.models.user_role import UserRole


class User(TimestampMixin, Base):
    """ORM model representing an application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )

    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
