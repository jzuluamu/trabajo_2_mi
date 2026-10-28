import pytest

from routing_service.domain.coverage.bfs import BreadthFirstReachability
from routing_service.domain.errors import NodeNotFoundError
from routing_service.domain.graph import Graph, Node, NodeType
from routing_service.domain.strategies import ReachabilityStrategy
from tests.demo_network import demo_graph

bfs = BreadthFirstReachability()


def _zones(*ids: str) -> Graph:
    graph = Graph()
    for node_id in ids:
        graph.add_node(Node(node_id, NodeType.ZONE, node_id))
    return graph


def test_implements_the_reachability_protocol() -> None:
    strategy: ReachabilityStrategy = bfs
    assert strategy.reachable_from(demo_graph(), "B_NORTE").origin == "B_NORTE"


def test_minimum_hops_in_the_demo_network() -> None:
    result = bfs.reachable_from(demo_graph(), "B_NORTE")

    assert result.hops == {
        "B_NORTE": 0,
        "Z_ALAMEDA": 1,
        "Z_CENTRO": 1,
        "Z_BOSQUE": 2,
        "Z_COLINA": 2,
        "Z_DELICIAS": 3,
        "B_SUR": 4,
        "Z_ESTACION": 4,
    }


def test_other_component_and_isolated_zone_are_not_reached() -> None:
    result = bfs.reachable_from(demo_graph(), "B_NORTE")

    assert not result.reaches("Z_FUENTE")
    assert not result.reaches("B_OESTE")
    assert not result.reaches("Z_ISLA")


def test_origin_without_edges_only_reaches_itself() -> None:
    assert bfs.reachable_from(demo_graph(), "Z_ISLA").hops == {"Z_ISLA": 0}


def test_one_way_edge_is_not_walked_backwards() -> None:
    result = bfs.reachable_from(demo_graph(), "Z_ESTACION")

    assert result.hops == {"Z_ESTACION": 0}


def test_weights_are_ignored_so_hops_beat_cost() -> None:
    result = bfs.reachable_from(demo_graph(), "B_NORTE")

    assert result.hops["Z_CENTRO"] == 1  # 30 min directo, 15 min por Alameda/Bosque


def test_cycle_terminates_without_repeating_nodes() -> None:
    graph = _zones("A", "B", "C")
    graph.add_edge("E1", "A", "B", 1)
    graph.add_edge("E2", "B", "C", 1)
    graph.add_edge("E3", "C", "A", 1)

    result = bfs.reachable_from(graph, "A", trace=True)

    assert result.hops == {"A": 0, "B": 1, "C": 1}
    enqueued = [step.node for step in result.trace if step.action == "enqueue"]
    assert sorted(n for n in enqueued if n) == ["A", "B", "C"]


def test_unknown_origin_raises_node_not_found() -> None:
    with pytest.raises(NodeNotFoundError) as error:
        bfs.reachable_from(demo_graph(), "B_NADA")

    assert error.value.code == "NODE_NOT_FOUND"


def test_trace_is_empty_unless_requested() -> None:
    assert bfs.reachable_from(demo_graph(), "B_NORTE").trace == ()


def test_trace_matches_the_table_in_docs_04() -> None:
    result = bfs.reachable_from(demo_graph(), "B_NORTE", trace=True)

    assert [(s.step, s.action, s.node, s.data["hops"]) for s in result.trace] == [
        (0, "enqueue", "B_NORTE", 0),
        (1, "visit", "B_NORTE", 0),
        (1, "enqueue", "Z_ALAMEDA", 1),
        (1, "enqueue", "Z_CENTRO", 1),
        (2, "visit", "Z_ALAMEDA", 1),
        (2, "enqueue", "Z_BOSQUE", 2),
        (3, "visit", "Z_CENTRO", 1),
        (3, "enqueue", "Z_COLINA", 2),
        (4, "visit", "Z_BOSQUE", 2),
        (5, "visit", "Z_COLINA", 2),
        (5, "enqueue", "Z_DELICIAS", 3),
        (6, "visit", "Z_DELICIAS", 3),
        (6, "enqueue", "B_SUR", 4),
        (6, "enqueue", "Z_ESTACION", 4),
        (7, "visit", "B_SUR", 4),
        (8, "visit", "Z_ESTACION", 4),
    ]
    assert result.trace[2].data["from"] == "B_NORTE"
