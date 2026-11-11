"""Camino de menos tramos — IMPLEMENTA: carril F3-A (docs/features/F3-sesiones.md).

BFS con predecesores que ignora los pesos; sirve para `fewest_hops` (docs/05).
La firma está CONGELADA (base de F3): el carril F3-A reemplaza solo el cuerpo de `find`.
"""

from routing_service.domain.graph import Graph
from routing_service.domain.results import PathResult


class BreadthFirstPathFinder:
    """Implementa `PathFinder`: el camino con el mínimo de tramos; `total_cost` = suma de pesos."""

    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult:
        raise NotImplementedError("F3-A: implementar el camino de menos tramos")
