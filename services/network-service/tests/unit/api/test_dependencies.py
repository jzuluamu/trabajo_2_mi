from network_service.api.dependencies import get_repository
from network_service.infrastructure.sql_repository import SqlAlchemyNetworkRepository


def test_repository_is_a_process_singleton() -> None:
    first = get_repository()

    assert get_repository() is first


def test_factory_uses_sql_repository() -> None:
    assert isinstance(get_repository(), SqlAlchemyNetworkRepository)
