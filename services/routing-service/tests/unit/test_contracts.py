"""Verifica que los puertos se pueden implementar estructuralmente (mypy valida las firmas).

Sirve de ejemplo para Feature 2 (BFS) y Feature 3 (Dijkstra): sus clases reales deben poder
asignarse a `ReachabilityStrategy` / `PathFinder` del mismo modo.
"""

from routing_service.application.ports import NetworkGateway
from routing_service.domain.graph import Graph, Node, NodeType
from routing_service.domain.results import PathResult, ReachabilityResult
from routing_service.domain.strategies import PathFinder, ReachabilityStrategy


class _OnlyOriginReach:
    def reachable_from(
        self, graph: Graph, origin: str, *, trace: bool = False
    ) -> ReachabilityResult:
        graph.require_node(origin)
        return ReachabilityResult(origin=origin, hops={origin: 0})


class _NeverFinds:
    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult:
        return PathResult(origin=origin, destination=destination, found=False)


class _InMemoryGateway:
    def load_graph(self) -> Graph:
        graph = Graph()
        graph.add_node(Node("B1", NodeType.BASE, "Base 1"))
        return graph


def test_fakes_satisfy_ports() -> None:
    gateway: NetworkGateway = _InMemoryGateway()
    reach: ReachabilityStrategy = _OnlyOriginReach()
    finder: PathFinder = _NeverFinds()

    graph = gateway.load_graph()

    assert reach.reachable_from(graph, "B1").hops == {"B1": 0}
    assert finder.find(graph, "B1", "Z1").found is False
