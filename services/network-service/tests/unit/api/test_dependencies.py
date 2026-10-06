from network_service.api.dependencies import get_repository
from network_service.infrastructure.memory_repository import InMemoryNetworkRepository


def test_repository_is_a_process_singleton() -> None:
    first = get_repository()

    assert get_repository() is first


def test_base_factory_uses_memory_repository() -> None:
    # F1-B cambia esta expectativa al activar PostgreSQL en infrastructure/factory.py.
    assert isinstance(get_repository(), InMemoryNetworkRepository)
