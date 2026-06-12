"""
Role ORM model.

Represents a system role used for access control and permissions,
defining what actions a user can perform within the platform.
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.audit import AuditMixin


class Role(Base, AuditMixin):
    __tablename__ = "roles"

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
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    user_roles = relationship(
        "UserRole",
        back_populates="role",
    )
