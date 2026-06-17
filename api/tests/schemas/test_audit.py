"""Tests for the shared audit schema."""

from app.schemas.audit import AuditSchema


def test_audit_schema_assigns_timestamps():
    audit = AuditSchema(created_at=1, updated_at=2)

    assert audit.created_at == 1
    assert audit.updated_at == 2
