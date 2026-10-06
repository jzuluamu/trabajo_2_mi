"""Suite de contrato (LSP) del puerto `NetworkRepository`. CONGELADA (base de F1).

Toda implementación debe pasarla sin modificaciones. Para usarla, cree una clase `Test...` que
herede de `RepositoryContract` y defina el fixture `repository` devolviendo un repositorio VACÍO
(ver tests/unit/infrastructure/test_memory_repository.py). Las conexiones siempre referencian
nodos existentes, para ser compatible con las FK de PostgreSQL.
"""

import pytest

from network_service.application.ports import NetworkRepository
from network_service.domain.errors import DuplicateIdError
from network_service.domain.models import Edge, Node, NodeType, Technician


def base(node_id: str, *technicians: Technician) -> Node:
    return Node(node_id, NodeType.BASE, f"Base {node_id}", technicians)


def zone(node_id: str) -> Node:
    return Node(node_id, NodeType.ZONE, f"Zona {node_id}")


def edge(edge_id: str, source: str, target: str, weight: float = 5.0, *, bi: bool = True) -> Edge:
    return Edge(edge_id, source, target, weight, bi)


ANA = Technician("T01", "Ana", True)
LUIS = Technician("T02", "Luis", False)


class RepositoryContract:
    def test_empty_repository(self, repository: NetworkRepository) -> None:
        assert repository.list_nodes() == []
        assert repository.list_edges() == []
        assert repository.get_node("B1") is None
        assert repository.get_edge("E1") is None
        assert repository.technician_exists("T01") is False

    def test_node_roundtrip_keeps_technicians_in_order(self, repository: NetworkRepository) -> None:
        node = base("B1", ANA, LUIS)

        repository.add_node(node)

        assert repository.get_node("B1") == node
        assert repository.technician_exists("T01")
        assert repository.technician_exists("T02")

    def test_zone_roundtrip_has_no_technicians(self, repository: NetworkRepository) -> None:
        repository.add_node(zone("Z1"))

        assert repository.get_node("Z1") == zone("Z1")

    def test_nodes_are_listed_sorted_by_id(self, repository: NetworkRepository) -> None:
        for node in (zone("Z2"), base("B1"), zone("Z1")):
            repository.add_node(node)

        assert [n.id for n in repository.list_nodes()] == ["B1", "Z1", "Z2"]

    def test_edge_roundtrip_keeps_weight_and_direction(self, repository: NetworkRepository) -> None:
        repository.add_node(zone("Z1"))
        repository.add_node(zone("Z2"))
        one_way = edge("E1", "Z1", "Z2", 7.5, bi=False)

        repository.add_edge(one_way)

        assert repository.get_edge("E1") == one_way

    def test_edges_are_listed_sorted_by_id(self, repository: NetworkRepository) -> None:
        for node in (zone("Z1"), zone("Z2"), zone("Z3")):
            repository.add_node(node)
        repository.add_edge(edge("E2", "Z2", "Z3"))
        repository.add_edge(edge("E1", "Z1", "Z2"))

        assert [e.id for e in repository.list_edges()] == ["E1", "E2"]

    def test_duplicate_node_id_raises(self, repository: NetworkRepository) -> None:
        repository.add_node(zone("Z1"))

        with pytest.raises(DuplicateIdError):
            repository.add_node(base("Z1"))

    def test_duplicate_edge_id_raises(self, repository: NetworkRepository) -> None:
        for node in (zone("Z1"), zone("Z2"), zone("Z3")):
            repository.add_node(node)
        repository.add_edge(edge("E1", "Z1", "Z2"))

        with pytest.raises(DuplicateIdError):
            repository.add_edge(edge("E1", "Z2", "Z3"))

    def test_duplicate_technician_across_nodes_raises_and_node_is_not_saved(
        self, repository: NetworkRepository
    ) -> None:
        repository.add_node(base("B1", ANA))

        with pytest.raises(DuplicateIdError):
            repository.add_node(base("B2", Technician("T01", "Otra Ana", True)))

        assert repository.get_node("B2") is None
        assert [n.id for n in repository.list_nodes()] == ["B1"]

    def test_delete_node_removes_its_technicians(self, repository: NetworkRepository) -> None:
        repository.add_node(base("B1", ANA))

        repository.delete_node("B1")

        assert repository.get_node("B1") is None
        assert repository.technician_exists("T01") is False

    def test_delete_edge(self, repository: NetworkRepository) -> None:
        repository.add_node(zone("Z1"))
        repository.add_node(zone("Z2"))
        repository.add_edge(edge("E1", "Z1", "Z2"))

        repository.delete_edge("E1")

        assert repository.get_edge("E1") is None
        assert repository.list_edges() == []

    def test_delete_missing_ids_is_a_noop(self, repository: NetworkRepository) -> None:
        repository.delete_node("NO_EXISTE")
        repository.delete_edge("NO_EXISTE")

        assert repository.list_nodes() == []

    def test_save_network_with_replace_discards_previous_state(
        self, repository: NetworkRepository
    ) -> None:
        repository.add_node(base("OLD", ANA))

        repository.save_network(
            [base("B1", LUIS), zone("Z1")], [edge("E1", "B1", "Z1")], replace=True
        )

        assert [n.id for n in repository.list_nodes()] == ["B1", "Z1"]
        assert [e.id for e in repository.list_edges()] == ["E1"]
        assert repository.technician_exists("T01") is False

    def test_save_network_without_replace_appends(self, repository: NetworkRepository) -> None:
        repository.add_node(zone("Z1"))

        repository.save_network([zone("Z2")], [edge("E1", "Z1", "Z2")], replace=False)

        assert [n.id for n in repository.list_nodes()] == ["Z1", "Z2"]
        assert [e.id for e in repository.list_edges()] == ["E1"]

    def test_save_network_is_atomic_when_appending(self, repository: NetworkRepository) -> None:
        repository.add_node(zone("Z1"))
        repository.add_node(zone("Z2"))
        repository.add_edge(edge("E1", "Z1", "Z2"))

        with pytest.raises(DuplicateIdError):
            repository.save_network([zone("Z3")], [edge("E1", "Z2", "Z3")], replace=False)

        assert [n.id for n in repository.list_nodes()] == ["Z1", "Z2"]
        assert [e.id for e in repository.list_edges()] == ["E1"]

    def test_save_network_is_atomic_when_replacing(self, repository: NetworkRepository) -> None:
        repository.add_node(base("B1", ANA))

        with pytest.raises(DuplicateIdError):
            repository.save_network([zone("Z1"), zone("Z1")], [], replace=True)

        assert [n.id for n in repository.list_nodes()] == ["B1"]
        assert repository.technician_exists("T01")
