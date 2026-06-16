"""
Shared router test fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """Provide a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client
