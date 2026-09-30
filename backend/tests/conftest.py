"""
Pytest Fixtures and Configuration for Agastya Test Suite
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.jobs.job_store import job_store


@pytest.fixture(autouse=True)
def reset_job_store():
    """Clears stored jobs and rate limits between tests."""
    with job_store._lock:
        job_store._jobs.clear()
    with job_store._rate_limit_lock:
        job_store._rate_limits.clear()
    yield


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client
