"""
Pytest configuration and shared fixtures for the test suite.
"""

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture(scope="session")
def client():
    """
    Session-wide FastAPI TestClient fixture.
    Triggers lifespan events (startup / shutdown) properly.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_markdown_content():
    """Provide sample markdown content for upload testing."""
    return "# Automated Test Document\nTested with pytest fixtures successfully."
