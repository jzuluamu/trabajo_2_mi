import os
from collections.abc import Iterator

import pytest

os.environ.update(
    {
        "NETWORK_SERVICE_URL": "http://network-service:8001",
        "ROUTING_SERVICE_URL": "http://routing-service:8002",
        "REQUEST_TIMEOUT_SECONDS": "0.5",
    }
)

from console.config import get_settings


@pytest.fixture(autouse=True)
def _fresh_settings() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
