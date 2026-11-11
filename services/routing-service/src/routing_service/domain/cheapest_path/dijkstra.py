"""Dijkstra de menor costo — IMPLEMENTA: carril F3-A (docs/features/F3-sesiones.md).

Justificación, pseudocódigo y traza esperada: docs/05-algoritmos-dijkstra.md.
La firma está CONGELADA (base de F3): el carril F3-A reemplaza solo el cuerpo de `find`.
"""

import heapq

from routing_service.domain.graph import Arc, Graph, validate_weight
from routing_service.domain.results import PathResult, TraceStep


class DijkstraPathFinder:
    """Implementa `PathFinder`: camino de menor suma de pesos (minutos), con `heapq`."""

    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult:
        graph.require_node(origin)  # NodeNotFoundError si no existen
        graph.require_node(destination)
        dist: dict[str, float] = {origin: 0.0}
        pred: dict[str, Arc] = {}  # pred[v] = arco usado para llegar a v con dist[v]
        heap: list[tuple[float, str]] = [(0.0, origin)]  # empate de costo: gana el menor id
        settled: set[str] = set()
        steps: list[TraceStep] = []

        step = 0
        while heap:
            cost, current = heapq.heappop(heap)
            if current in settled:  # entrada obsoleta ("lazy deletion")
                if trace:
                    steps.append(TraceStep(step, "stale", current, {"cost": cost}))
                continue
            settled.add(current)
            step += 1
            if trace:
                steps.append(TraceStep(step, "pop", current, {"cost": cost}))
            if current == destination:  # salida temprana: el destino ya es definitivo
                break
            for arc in graph.neighbors(current):
                validate_weight(arc.weight, arc.edge_id)  # un peso <= 0 invalida Dijkstra
                candidate = cost + float(arc.weight)
                best = dist.get(arc.target)
                if best is not None and candidate >= best:
                    if trace:
                        steps.append(
                            TraceStep(
                                step,
                                "skip",
                                arc.target,
                                {"cost": candidate, "best": best, "from": current},
                            )
                        )
                    continue
                dist[arc.target] = candidate
                pred[arc.target] = arc
                heapq.heappush(heap, (candidate, arc.target))
                if trace:
                    data: dict[str, object] = {
                        "cost": candidate,
                        "from": current,
                        "edge_id": arc.edge_id,
                    }
                    if best is not None:
                        data["previous"] = best
                    steps.append(TraceStep(step, "relax", arc.target, data))

        if destination not in settled:
            return PathResult(origin, destination, found=False, trace=tuple(steps))
        legs = reconstruct_legs(destination, origin, pred)
        return PathResult(
            origin,
            destination,
            found=True,
            path=(origin, *(arc.target for arc in legs)),
            total_cost=dist[destination],
            trace=tuple(steps),
            legs=legs,
        )


def reconstruct_legs(destination: str, origin: str, pred: dict[str, Arc]) -> tuple[Arc, ...]:
    """Sigue `pred` desde el destino hasta el origen y devuelve los arcos en orden de recorrido."""
    legs: list[Arc] = []
    node = destination
    while node != origin:
        arc = pred[node]
        legs.append(arc)
        node = arc.source
    return tuple(reversed(legs))
