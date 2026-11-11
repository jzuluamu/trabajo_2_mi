"""Camino de menos tramos — IMPLEMENTA: carril F3-A (docs/features/F3-sesiones.md).

BFS con predecesores que ignora los pesos; sirve para `fewest_hops` (docs/05).
La firma está CONGELADA (base de F3): el carril F3-A reemplaza solo el cuerpo de `find`.
"""

from collections import deque

from routing_service.domain.cheapest_path.dijkstra import reconstruct_legs
from routing_service.domain.graph import Arc, Graph
from routing_service.domain.results import PathResult, TraceStep


class BreadthFirstPathFinder:
    """Implementa `PathFinder`: el camino con el mínimo de tramos; `total_cost` = suma de pesos."""

    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult:
        graph.require_node(origin)  # NodeNotFoundError si no existen
        graph.require_node(destination)
        pred: dict[str, Arc] = {}
        discovered: set[str] = {origin}
        queue: deque[str] = deque([origin])
        steps: list[TraceStep] = []
        if trace:
            steps.append(TraceStep(0, "enqueue", origin, {"hops": 0}))

        step = 0
        while queue and destination not in discovered:
            step += 1
            current = queue.popleft()
            if trace:
                steps.append(TraceStep(step, "visit", current, {}))
            # Vecinos ordenados por id: entre caminos de igual largo gana el primero en ese orden.
            for arc in graph.neighbors(current):
                if arc.target in discovered:
                    continue
                discovered.add(arc.target)
                pred[arc.target] = arc
                queue.append(arc.target)
                if trace:
                    steps.append(TraceStep(step, "enqueue", arc.target, {"from": current}))
                if arc.target == destination:  # para al descubrir el destino
                    break

        if destination not in discovered:
            return PathResult(origin, destination, found=False, trace=tuple(steps))
        legs = reconstruct_legs(destination, origin, pred)
        return PathResult(
            origin,
            destination,
            found=True,
            path=(origin, *(arc.target for arc in legs)),
            total_cost=float(sum(arc.weight for arc in legs)),
            trace=tuple(steps),
            legs=legs,
        )
