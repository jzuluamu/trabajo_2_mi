import pytest

from network_service.infrastructure.memory_repository import InMemoryNetworkRepository
from tests.contract.repository_contract import RepositoryContract


class TestInMemoryRepository(RepositoryContract):
    @pytest.fixture
    def repository(self) -> InMemoryNetworkRepository:
        return InMemoryNetworkRepository()
