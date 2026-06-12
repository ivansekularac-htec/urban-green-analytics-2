"""
common.py
Shared SQLAlchemy model utilities.

This module contains reusable constants and helpers shared
across ORM model definitions.
"""

from sqlalchemy import text

TIMESTAMP_DEFAULT = text("(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)")
