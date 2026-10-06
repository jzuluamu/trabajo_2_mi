"""Puertos de los algoritmos (OCP/Strategy): nuevas variantes se agregan sin tocar los casos de uso.

- Feature 2 implementa `ReachabilityStrategy` en `domain/coverage/` (BFS).
- Feature 3 implementa `PathFinder` en `domain/cheapest_path/` (Dijkstra).
"""

from typing import Protocol

from routing_service.domain.graph import Graph
from routing_service.domain.results import PathResult, ReachabilityResult


class ReachabilityStrategy(Protocol):
    def reachable_from(
        self, graph: Graph, origin: str, *, trace: bool = False
    ) -> ReachabilityResult: ...


class PathFinder(Protocol):
    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult: ...
