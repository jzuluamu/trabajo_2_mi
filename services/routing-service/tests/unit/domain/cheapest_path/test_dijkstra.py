import math

import pytest

from routing_service.domain.cheapest_path.dijkstra import DijkstraPathFinder
from routing_service.domain.cheapest_path.fewest_hops import BreadthFirstPathFinder
from routing_service.domain.errors import InvalidWeightError, NodeNotFoundError
from routing_service.domain.graph import Arc, Graph, Node, NodeType
from routing_service.domain.results import TraceStep
from routing_service.domain.strategies import PathFinder
from tests.demo_network import demo_graph

dijkstra = DijkstraPathFinder()


def _zones(*ids: str) -> Graph:
    graph = Graph()
    for node_id in ids:
        graph.add_node(Node(node_id, NodeType.ZONE, node_id))
    return graph


def test_implements_the_path_finder_protocol() -> None:
    finder: PathFinder = dijkstra
    assert finder.find(demo_graph(), "B_NORTE", "Z_CENTRO").found


def test_cheapest_route_in_the_demo_network() -> None:
    result = dijkstra.find(demo_graph(), "B_NORTE", "Z_CENTRO")

    assert result.found
    assert result.origin == "B_NORTE"
    assert result.destination == "Z_CENTRO"
    assert result.path == ("B_NORTE", "Z_ALAMEDA", "Z_BOSQUE", "Z_CENTRO")
    assert result.total_cost == 15.0
    assert isinstance(result.total_cost, float)
    assert result.hops == 3
    assert result.legs == (
        Arc("E02", "B_NORTE", "Z_ALAMEDA", 5),
        Arc("E03", "Z_ALAMEDA", "Z_BOSQUE", 5),
        Arc("E04", "Z_BOSQUE", "Z_CENTRO", 5),
    )


def test_fewer_hops_is_not_cheaper() -> None:
    graph = demo_graph()
    cheapest = dijkstra.find(graph, "B_NORTE", "Z_CENTRO")
    shortest = BreadthFirstPathFinder().find(graph, "B_NORTE", "Z_CENTRO")

    assert shortest.path == ("B_NORTE", "Z_CENTRO")
    assert shortest.hops is not None and cheapest.hops is not None
    assert shortest.hops < cheapest.hops
    assert shortest.total_cost is not None and cheapest.total_cost is not None
    assert shortest.total_cost > cheapest.total_cost
    assert (shortest.total_cost, cheapest.total_cost) == (30.0, 15.0)


def test_legs_chain_the_path() -> None:
    result = dijkstra.find(demo_graph(), "B_NORTE", "Z_ESTACION")

    assert result.path == (
        "B_NORTE",
        "Z_ALAMEDA",
        "Z_BOSQUE",
        "Z_CENTRO",
        "Z_COLINA",
        "Z_DELICIAS",
        "Z_ESTACION",
    )
    assert [leg.edge_id for leg in result.legs] == ["E02", "E03", "E04", "E05", "E07", "E08"]
    for i, leg in enumerate(result.legs):
        assert (leg.source, leg.target) == (result.path[i], result.path[i + 1])
    assert result.total_cost == sum(leg.weight for leg in result.legs) == 44.0


def test_disconnected_network_is_not_found_without_error() -> None:
    result = dijkstra.find(demo_graph(), "B_NORTE", "Z_FUENTE")

    assert not result.found
    assert result.path == ()
    assert result.total_cost is None
    assert result.hops is None
    assert result.legs == ()
    assert result.trace == ()


def test_isolated_zone_is_not_found() -> None:
    assert not dijkstra.find(demo_graph(), "B_SUR", "Z_ISLA").found


def test_one_way_edge_only_in_its_direction() -> None:
    graph = demo_graph()
    forward = dijkstra.find(graph, "B_SUR", "Z_ESTACION")
    backward = dijkstra.find(graph, "Z_ESTACION", "B_SUR")

    assert forward.path == ("B_SUR", "Z_DELICIAS", "Z_ESTACION")
    assert forward.total_cost == 15.0
    assert [leg.edge_id for leg in forward.legs] == ["E06", "E08"]
    assert not backward.found


def test_origin_equals_destination() -> None:
    result = dijkstra.find(demo_graph(), "B_NORTE", "B_NORTE", trace=True)

    assert result.found
    assert result.path == ("B_NORTE",)
    assert result.total_cost == 0.0
    assert result.hops == 0
    assert result.legs == ()
    assert result.trace == (TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),)


def test_unknown_origin_raises_node_not_found() -> None:
    with pytest.raises(NodeNotFoundError) as exc:
        dijkstra.find(demo_graph(), "B_NADA", "Z_CENTRO")

    assert exc.value.code == "NODE_NOT_FOUND"
    assert exc.value.details == {"node_id": "B_NADA"}


def test_unknown_destination_raises_node_not_found() -> None:
    with pytest.raises(NodeNotFoundError) as exc:
        dijkstra.find(demo_graph(), "B_NORTE", "Z_NADA")

    assert exc.value.details == {"node_id": "Z_NADA"}


@pytest.mark.parametrize("weight", [0, -5, math.inf, math.nan])
def test_invalid_weight_is_rejected(weight: float) -> None:
    graph = _zones("A", "B")
    graph._adjacency["A"].append(Arc("E_BAD", "A", "B", weight))

    with pytest.raises(InvalidWeightError) as exc:
        dijkstra.find(graph, "A", "B")

    assert exc.value.code == "INVALID_WEIGHT"
    assert exc.value.details["edge_id"] == "E_BAD"


def test_invalid_weight_is_rejected_even_if_a_valid_path_exists() -> None:
    graph = _zones("A", "B", "C")
    graph.add_edge("E1", "A", "C", 1, bidirectional=False)
    graph._adjacency["A"].append(Arc("E_BAD", "A", "B", -1))

    with pytest.raises(InvalidWeightError):
        dijkstra.find(graph, "A", "C")


def test_trace_matches_the_table_in_docs_05() -> None:
    result = dijkstra.find(demo_graph(), "B_NORTE", "Z_CENTRO", trace=True)

    assert result.trace == (
        TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),
        TraceStep(1, "relax", "Z_ALAMEDA", {"cost": 5.0, "from": "B_NORTE", "edge_id": "E02"}),
        TraceStep(1, "relax", "Z_CENTRO", {"cost": 30.0, "from": "B_NORTE", "edge_id": "E01"}),
        TraceStep(2, "pop", "Z_ALAMEDA", {"cost": 5.0}),
        TraceStep(2, "skip", "B_NORTE", {"cost": 10.0, "best": 0.0, "from": "Z_ALAMEDA"}),
        TraceStep(2, "relax", "Z_BOSQUE", {"cost": 10.0, "from": "Z_ALAMEDA", "edge_id": "E03"}),
        TraceStep(3, "pop", "Z_BOSQUE", {"cost": 10.0}),
        TraceStep(3, "skip", "Z_ALAMEDA", {"cost": 15.0, "best": 5.0, "from": "Z_BOSQUE"}),
        TraceStep(
            3,
            "relax",
            "Z_CENTRO",
            {"cost": 15.0, "from": "Z_BOSQUE", "edge_id": "E04", "previous": 30.0},
        ),
        TraceStep(4, "pop", "Z_CENTRO", {"cost": 15.0}),
    )
    assert all(isinstance(step.data["cost"], float) for step in result.trace)


def test_no_trace_unless_requested() -> None:
    assert dijkstra.find(demo_graph(), "B_NORTE", "Z_CENTRO").trace == ()


def test_stale_heap_entry_is_traced_and_discarded() -> None:
    result = dijkstra.find(demo_graph(), "B_NORTE", "Z_DELICIAS", trace=True)

    stale = [step for step in result.trace if step.action == "stale"]
    assert stale == [TraceStep(5, "stale", "Z_CENTRO", {"cost": 30.0})]
    pops = [step.node for step in result.trace if step.action == "pop"]
    assert pops.count("Z_CENTRO") == 1
    assert pops[-1] == "Z_DELICIAS"
    assert result.total_cost == 37.0


def test_trace_is_kept_when_destination_is_not_found() -> None:
    result = dijkstra.find(demo_graph(), "B_OESTE", "Z_ISLA", trace=True)

    assert not result.found
    assert result.trace == (
        TraceStep(1, "pop", "B_OESTE", {"cost": 0.0}),
        TraceStep(1, "relax", "Z_FUENTE", {"cost": 6.0, "from": "B_OESTE", "edge_id": "E09"}),
        TraceStep(2, "pop", "Z_FUENTE", {"cost": 6.0}),
        TraceStep(2, "skip", "B_OESTE", {"cost": 12.0, "best": 0.0, "from": "Z_FUENTE"}),
    )


@pytest.mark.parametrize("first", ["B", "C"])
def test_ties_are_broken_by_node_id(first: str) -> None:
    graph = _zones("A", "B", "C", "D")
    second = "C" if first == "B" else "B"
    for node in (first, second):  # el orden de inserción no influye
        graph.add_edge(f"E_A{node}", "A", node, 1, bidirectional=False)
        graph.add_edge(f"E_{node}D", node, "D", 1, bidirectional=False)

    result = dijkstra.find(graph, "A", "D")

    assert result.path == ("A", "B", "D")
    assert result.total_cost == 2.0


@pytest.mark.parametrize(
    ("zone", "costs"),
    [
        ("Z_COLINA", {"B_NORTE": 25.0, "B_SUR": 20.0}),
        ("Z_ESTACION", {"B_NORTE": 44.0, "B_SUR": 15.0}),
        ("Z_FUENTE", {"B_NORTE": None, "B_SUR": None, "B_OESTE": 6.0}),
        ("Z_ISLA", {"B_NORTE": None, "B_SUR": None, "B_OESTE": None}),
    ],
)
def test_costs_from_each_base_for_the_attention_examples(
    zone: str, costs: dict[str, float | None]
) -> None:
    graph = demo_graph()

    assert {base: dijkstra.find(graph, base, zone).total_cost for base in costs} == costs
