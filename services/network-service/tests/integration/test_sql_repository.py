"""Integración del repositorio SQL contra PostgreSQL real (F1-B).

Requiere `TEST_DATABASE_URL` (`make test-network` la define con `network-db`).
Sin esa variable, estas pruebas se omiten (ver `tests/integration/conftest.py`).
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, insert, select, text
from sqlalchemy.exc import IntegrityError

from network_service.infrastructure.database import create_db_engine
from network_service.infrastructure.orm import EdgeRow, NodeRow, TechnicianRow
from network_service.infrastructure.sql_repository import SqlAlchemyNetworkRepository
from tests.contract.repository_contract import ANA, RepositoryContract, base, edge, zone

SERVICE_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session", autouse=True)
def _migrated_schema(database_url: str) -> None:
    """Aplica `alembic upgrade head` una vez por sesión (como `test_migrations.py`)."""
    config = Config(str(SERVICE_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def _fresh_repository(database_url: str) -> SqlAlchemyNetworkRepository:
    engine = create_db_engine(database_url)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE edges, technicians, nodes"))
    return SqlAlchemyNetworkRepository(engine)


class TestSqlAlchemyRepository(RepositoryContract):
    @pytest.fixture
    def repository(self, database_url: str) -> SqlAlchemyNetworkRepository:
        return _fresh_repository(database_url)


@pytest.mark.parametrize("weight", [0, -5, 1441])
def test_check_weight_range_rejected(database_url: str, weight: float) -> None:
    repo = _fresh_repository(database_url)
    repo.add_node(zone("Z1"))
    repo.add_node(zone("Z2"))
    engine = create_db_engine(database_url)
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            insert(EdgeRow).values(
                id="E_BAD", source="Z1", target="Z2", weight=weight, bidirectional=True
            )
        )


def test_check_no_self_loop_rejected(database_url: str) -> None:
    repo = _fresh_repository(database_url)
    repo.add_node(zone("Z1"))
    engine = create_db_engine(database_url)
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            insert(EdgeRow).values(
                id="E_LOOP", source="Z1", target="Z1", weight=5, bidirectional=True
            )
        )


def test_unique_source_target_rejected(database_url: str) -> None:
    repo = _fresh_repository(database_url)
    repo.add_node(zone("Z1"))
    repo.add_node(zone("Z2"))
    repo.add_edge(edge("E1", "Z1", "Z2"))
    engine = create_db_engine(database_url)
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            insert(EdgeRow).values(id="E2", source="Z1", target="Z2", weight=5, bidirectional=True)
        )


def test_check_node_type_rejected(database_url: str) -> None:
    _fresh_repository(database_url)
    engine = create_db_engine(database_url)
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(insert(NodeRow).values(id="X1", type="OTRO", name="Otro"))


def test_delete_node_with_edges_fails_restrict(database_url: str) -> None:
    repo = _fresh_repository(database_url)
    repo.add_node(zone("Z1"))
    repo.add_node(zone("Z2"))
    repo.add_edge(edge("E1", "Z1", "Z2"))
    engine = create_db_engine(database_url)
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(delete(NodeRow).where(NodeRow.id == "Z1"))


def test_delete_base_cascades_technicians(database_url: str) -> None:
    repo = _fresh_repository(database_url)
    repo.add_node(base("B1", ANA))
    engine = create_db_engine(database_url)
    with engine.begin() as conn:
        conn.execute(delete(NodeRow).where(NodeRow.id == "B1"))
    with engine.connect() as conn:
        remaining = conn.scalars(select(TechnicianRow).where(TechnicianRow.node_id == "B1")).all()
    assert remaining == []


def test_data_persists_between_instances(database_url: str) -> None:
    first = _fresh_repository(database_url)
    first.add_node(base("B1", ANA))
    first.add_node(zone("Z1"))
    first.add_edge(edge("E1", "B1", "Z1"))

    second = SqlAlchemyNetworkRepository(create_db_engine(database_url))

    assert second.get_node("B1") == base("B1", ANA)
    assert [n.id for n in second.list_nodes()] == ["B1", "Z1"]
    assert second.get_edge("E1") == edge("E1", "B1", "Z1")
