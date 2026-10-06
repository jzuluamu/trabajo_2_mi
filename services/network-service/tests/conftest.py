import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

TEST_ENV = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/test",
    "COORDINATOR_API_KEY": "test-coordinator-key-0001",
    "OPERATOR_API_KEY": "test-operator-key-000002",
    "INTERNAL_API_KEY": "test-internal-key-000003",
}
os.environ.update(TEST_ENV)

from network_service.api.dependencies import _repository_singleton  # noqa: E402
from network_service.config import get_settings  # noqa: E402
from network_service.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_settings() -> Iterator[None]:
    """Cada prueba arranca con configuración y repositorio (en memoria) nuevos."""
    get_settings.cache_clear()
    _repository_singleton.cache_clear()
    yield
    get_settings.cache_clear()
    _repository_singleton.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def coordinator_headers() -> dict[str, str]:
    return {"X-API-Key": TEST_ENV["COORDINATOR_API_KEY"]}


@pytest.fixture
def operator_headers() -> dict[str, str]:
    return {"X-API-Key": TEST_ENV["OPERATOR_API_KEY"]}


@pytest.fixture
def internal_headers() -> dict[str, str]:
    return {"X-API-Key": TEST_ENV["INTERNAL_API_KEY"]}
