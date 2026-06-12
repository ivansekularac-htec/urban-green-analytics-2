"""
role.py
SQLAlchemy ORM model for the roles table.

This module defines the Role entity used to manage user roles
within the Urban Green Analytics platform.
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TIMESTAMP_DEFAULT

if TYPE_CHECKING:
    from app.models.user_role import UserRole


class Role(Base):
    """ORM model for the roles table."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
    )

    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role")
