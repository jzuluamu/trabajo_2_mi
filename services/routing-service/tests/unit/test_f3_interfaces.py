"""Vigila las interfaces CONGELADAS de la base de F3 (docs/features/F3-menor-costo.md).

Si esta prueba falla, un carril cambió una firma que otro carril usa: revierta el cambio o
proponga un PR `contract-change`. No la modifique para hacerla pasar.
"""

import inspect
from dataclasses import fields

from routing_service.application.attention import (
    AlternativeBase,
    AttentionReport,
    AvailableTechnician,
    BestBase,
    FindBestAttention,
)
from routing_service.application.routes import FewestHops, FindCheapestRoute, Leg, RouteReport
from routing_service.domain.cheapest_path.dijkstra import DijkstraPathFinder
from routing_service.domain.cheapest_path.fewest_hops import BreadthFirstPathFinder
from routing_service.domain.errors import DestinationNotFoundError
from routing_service.domain.graph import Arc, Graph
from routing_service.domain.results import PathResult
from routing_service.domain.strategies import PathFinder


def _names(cls: type) -> list[str]:
    return [f.name for f in fields(cls)]


def _params(function: object) -> list[str]:
    return list(inspect.signature(function).parameters)  # type: ignore[arg-type]


def test_path_result_carries_the_legs() -> None:
    arc = Arc("E1", "A", "B", 5.0)
    result = PathResult("A", "B", True, ("A", "B"), 5.0, (), (arc,))

    assert _names(PathResult) == [
        "origin", "destination", "found", "path", "total_cost", "trace", "legs",
    ]  # fmt: skip
    assert result.legs == (arc,)
    assert PathResult("A", "B", False).legs == ()


def test_destination_not_found_code() -> None:
    assert DestinationNotFoundError("x").code == "DESTINATION_NOT_FOUND"


def test_path_finders_signature() -> None:
    finders: list[PathFinder] = [DijkstraPathFinder(), BreadthFirstPathFinder()]
    for finder in finders:
        assert _params(finder.find) == ["graph", "origin", "destination", "trace"]


def test_route_report_shape() -> None:
    assert _names(Leg) == ["edge_id", "source", "target", "weight"]
    assert _names(FewestHops) == ["path", "hops", "cost"]
    assert _names(RouteReport) == [
        "found", "origin", "destination", "path", "total_cost", "hops", "legs", "fewest_hops",
        "message", "trace",
    ]  # fmt: skip


def test_attention_report_shape() -> None:
    assert _names(AvailableTechnician) == ["id", "name"]
    assert _names(BestBase) == ["base", "technicians", "path", "total_cost", "hops"]
    assert _names(AlternativeBase) == ["base", "total_cost", "hops"]
    assert _names(AttentionReport) == [
        "zone", "found", "best", "alternatives", "message", "trace",
    ]  # fmt: skip


class _Gateway:
    def load_graph(self) -> Graph:
        return Graph()


def test_use_case_constructors_and_execute_signatures() -> None:
    finder = DijkstraPathFinder()
    route = FindCheapestRoute(_Gateway(), finder, BreadthFirstPathFinder())
    attention = FindBestAttention(_Gateway(), finder)

    assert _params(FindCheapestRoute.__init__) == [
        "self", "gateway", "path_finder", "fewest_hops_finder",
    ]  # fmt: skip
    assert _params(route.execute) == ["origin", "destination", "trace"]
    assert _params(FindBestAttention.__init__) == ["self", "gateway", "path_finder"]
    assert _params(attention.execute) == ["zone", "trace"]
