"""
role.py
SQLAlchemy ORM model for the roles table.

This module defines the Role entity used to manage user roles
within the Urban Green Analytics platform.
"""

from sqlalchemy import (
    BigInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.mixins import TimestampMixin
from app.models.user_role import UserRole


class Role(TimestampMixin, Base):
    """ORM model for the roles table."""

    __tablename__ = "roles"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="role",
    )
