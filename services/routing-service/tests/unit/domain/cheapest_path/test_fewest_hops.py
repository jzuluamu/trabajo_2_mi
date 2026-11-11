import pytest

from routing_service.domain.cheapest_path.fewest_hops import BreadthFirstPathFinder
from routing_service.domain.errors import NodeNotFoundError
from routing_service.domain.graph import Arc, Graph, Node, NodeType
from routing_service.domain.results import TraceStep
from routing_service.domain.strategies import PathFinder
from tests.demo_network import demo_graph

bfs = BreadthFirstPathFinder()


def _zones(*ids: str) -> Graph:
    graph = Graph()
    for node_id in ids:
        graph.add_node(Node(node_id, NodeType.ZONE, node_id))
    return graph


def test_implements_the_path_finder_protocol() -> None:
    finder: PathFinder = bfs
    assert finder.find(demo_graph(), "B_NORTE", "Z_CENTRO").found


def test_fewest_hops_ignores_weights() -> None:
    result = bfs.find(demo_graph(), "B_NORTE", "Z_CENTRO")

    assert result.found
    assert result.path == ("B_NORTE", "Z_CENTRO")
    assert result.hops == 1
    assert result.legs == (Arc("E01", "B_NORTE", "Z_CENTRO", 30),)
    assert result.total_cost == 30.0
    assert isinstance(result.total_cost, float)


def test_total_cost_is_the_sum_of_the_path_weights() -> None:
    result = bfs.find(demo_graph(), "B_NORTE", "Z_COLINA")

    assert result.path == ("B_NORTE", "Z_CENTRO", "Z_COLINA")
    assert [leg.edge_id for leg in result.legs] == ["E01", "E05"]
    assert result.total_cost == 40.0


def test_disconnected_network_is_not_found_without_error() -> None:
    result = bfs.find(demo_graph(), "B_NORTE", "Z_FUENTE")

    assert not result.found
    assert result.path == ()
    assert result.total_cost is None
    assert result.hops is None
    assert result.legs == ()
    assert result.trace == ()


def test_one_way_edge_only_in_its_direction() -> None:
    graph = demo_graph()

    assert bfs.find(graph, "B_SUR", "Z_ESTACION").path == ("B_SUR", "Z_DELICIAS", "Z_ESTACION")
    assert not bfs.find(graph, "Z_ESTACION", "B_SUR").found


def test_origin_equals_destination() -> None:
    result = bfs.find(demo_graph(), "Z_ISLA", "Z_ISLA", trace=True)

    assert result.found
    assert result.path == ("Z_ISLA",)
    assert result.total_cost == 0.0
    assert result.legs == ()
    assert result.trace == (TraceStep(0, "enqueue", "Z_ISLA", {"hops": 0}),)


@pytest.mark.parametrize(("origin", "destination"), [("B_NADA", "Z_CENTRO"), ("B_NORTE", "Z_NADA")])
def test_unknown_node_raises_node_not_found(origin: str, destination: str) -> None:
    with pytest.raises(NodeNotFoundError):
        bfs.find(demo_graph(), origin, destination)


def test_trace_stops_when_the_destination_is_discovered() -> None:
    result = bfs.find(demo_graph(), "B_NORTE", "Z_CENTRO", trace=True)

    assert result.trace == (
        TraceStep(0, "enqueue", "B_NORTE", {"hops": 0}),
        TraceStep(1, "visit", "B_NORTE", {}),
        TraceStep(1, "enqueue", "Z_ALAMEDA", {"from": "B_NORTE"}),
        TraceStep(1, "enqueue", "Z_CENTRO", {"from": "B_NORTE"}),
    )


def test_trace_of_a_deeper_search() -> None:
    result = bfs.find(demo_graph(), "B_SUR", "Z_ESTACION", trace=True)

    assert result.trace == (
        TraceStep(0, "enqueue", "B_SUR", {"hops": 0}),
        TraceStep(1, "visit", "B_SUR", {}),
        TraceStep(1, "enqueue", "Z_DELICIAS", {"from": "B_SUR"}),
        TraceStep(2, "visit", "Z_DELICIAS", {}),
        TraceStep(2, "enqueue", "Z_COLINA", {"from": "Z_DELICIAS"}),
        TraceStep(2, "enqueue", "Z_ESTACION", {"from": "Z_DELICIAS"}),
    )


def test_no_trace_unless_requested() -> None:
    assert bfs.find(demo_graph(), "B_SUR", "Z_ESTACION").trace == ()


@pytest.mark.parametrize("first", ["B", "C"])
def test_ties_are_broken_by_node_id(first: str) -> None:
    graph = _zones("A", "B", "C", "D")
    second = "C" if first == "B" else "B"
    for node in (first, second):  # el orden de inserción no influye
        graph.add_edge(f"E_A{node}", "A", node, 9 if node == "B" else 1, bidirectional=False)
        graph.add_edge(f"E_{node}D", node, "D", 1, bidirectional=False)

    result = bfs.find(graph, "A", "D")

    assert result.path == ("A", "B", "D")
    assert result.total_cost == 10.0
