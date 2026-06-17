"""
User ORM model.

Represents an application user with authentication credentials
and profile information, and serves as the base entity for role
and permission assignment within the system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.users.user_roles import UserRole


class User(Base, AuditMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="user",
    )
