import math

import pytest

from routing_service.domain.errors import (
    DuplicateNodeError,
    InvalidWeightError,
    NodeNotFoundError,
)
from routing_service.domain.graph import Arc, Graph, Node, NodeType, Technician
from routing_service.domain.results import PathResult, ReachabilityResult


@pytest.fixture
def graph() -> Graph:
    g = Graph()
    g.add_node(
        Node(
            "B1",
            NodeType.BASE,
            "Base 1",
            (Technician("T1", "Ana", True), Technician("T2", "Luis", False)),
        )
    )
    g.add_node(Node("Z1", NodeType.ZONE, "Zona 1"))
    g.add_node(Node("Z2", NodeType.ZONE, "Zona 2"))
    return g


def test_bidirectional_edge_creates_two_arcs(graph: Graph) -> None:
    graph.add_edge("E1", "B1", "Z1", 5)

    assert graph.neighbors("B1") == (Arc("E1", "B1", "Z1", 5),)
    assert graph.neighbors("Z1") == (Arc("E1", "Z1", "B1", 5),)


def test_one_way_edge_creates_a_single_arc(graph: Graph) -> None:
    graph.add_edge("E1", "Z1", "Z2", 3, bidirectional=False)

    assert graph.neighbors("Z1") == (Arc("E1", "Z1", "Z2", 3),)
    assert graph.neighbors("Z2") == ()


def test_neighbors_are_sorted_for_deterministic_traversal(graph: Graph) -> None:
    graph.add_edge("E2", "B1", "Z2", 1)
    graph.add_edge("E1", "B1", "Z1", 9)

    assert [arc.target for arc in graph.neighbors("B1")] == ["Z1", "Z2"]
    assert len(list(graph.arcs())) == 4


@pytest.mark.parametrize("weight", [0, -1, math.inf, math.nan])
def test_invalid_weights_are_rejected(graph: Graph, weight: float) -> None:
    with pytest.raises(InvalidWeightError) as error:
        graph.add_edge("E1", "B1", "Z1", weight)

    assert error.value.code == "INVALID_WEIGHT"
    assert error.value.details["edge_id"] == "E1"


def test_edge_to_unknown_node_is_rejected(graph: Graph) -> None:
    with pytest.raises(NodeNotFoundError, match="Z9"):
        graph.add_edge("E1", "B1", "Z9", 1)


def test_duplicate_node_is_rejected(graph: Graph) -> None:
    with pytest.raises(DuplicateNodeError):
        graph.add_node(Node("B1", NodeType.BASE, "Otra"))


def test_node_queries(graph: Graph) -> None:
    assert graph.has_node("Z1")
    assert not graph.has_node("Z9")
    assert [n.id for n in graph.nodes()] == ["B1", "Z1", "Z2"]
    assert [t.id for t in graph.require_node("B1").available_technicians] == ["T1"]
    with pytest.raises(NodeNotFoundError):
        graph.neighbors("Z9")


def test_results_helpers() -> None:
    reach = ReachabilityResult(origin="B1", hops={"B1": 0, "Z1": 1})
    found = PathResult("B1", "Z2", True, ("B1", "Z1", "Z2"), 8.0)
    missing = PathResult("B1", "Z9", False)

    assert reach.reaches("Z1") and not reach.reaches("Z2")
    assert found.hops == 2
    assert missing.hops is None
