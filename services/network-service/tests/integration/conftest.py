"""Fixtures de integración con PostgreSQL. `make test-network` define TEST_DATABASE_URL
(servicio `network-db` de docker-compose.test.yml). Sin esa variable, estas pruebas se omiten."""

import os

import pytest


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no definida: ejecute `make test-network`.")
    return url
