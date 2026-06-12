"""
user.py
SQLAlchemy ORM model for the users table.

This module defines the User entity used for application
authentication and authorization.
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.user_role import UserRole


class User(Base, TimestampMixin):
    """ORM model for the users table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user")
