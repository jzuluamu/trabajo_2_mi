"""Dijkstra de menor costo — IMPLEMENTA: carril F3-A (docs/features/F3-sesiones.md).

Justificación, pseudocódigo y traza esperada: docs/05-algoritmos-dijkstra.md.
La firma está CONGELADA (base de F3): el carril F3-A reemplaza solo el cuerpo de `find`.
"""

from routing_service.domain.graph import Graph
from routing_service.domain.results import PathResult


class DijkstraPathFinder:
    """Implementa `PathFinder`: camino de menor suma de pesos (minutos), con `heapq`."""

    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult:
        raise NotImplementedError("F3-A: implementar Dijkstra")
