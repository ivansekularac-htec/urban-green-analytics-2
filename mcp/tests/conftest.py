"""Shared pytest fixtures for the MCP test suite.

Clears get_settings/get_client caches around every test so one failure
cannot poison later tests with a stale cached Settings or client.
"""

import pytest

from app.clickhouse import get_client
from app.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_and_client_caches():
    get_settings.cache_clear()
    get_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_client.cache_clear()
