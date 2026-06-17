"""Tests for the shared audit mixin."""

from datetime import UTC, datetime
from unittest.mock import patch

from app.models.common.audit import epoch_now


def test_epoch_now_returns_current_unix_timestamp():
    fixed = datetime(2026, 6, 17, 12, 0, 0, tzinfo=UTC)

    with patch("app.models.common.audit.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed

        result = epoch_now()

    assert result == int(fixed.timestamp())


def test_epoch_now_returns_integer():
    assert isinstance(epoch_now(), int)
