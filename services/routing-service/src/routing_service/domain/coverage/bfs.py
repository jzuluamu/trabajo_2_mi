"""BFS de alcance (Feature 2; justificación y traza en docs/04-algoritmos-bfs.md)."""

from collections import deque

from routing_service.domain.graph import Graph
from routing_service.domain.results import ReachabilityResult, TraceStep


class BreadthFirstReachability:
    """Implementa `ReachabilityStrategy`: nodos alcanzables con el mínimo de tramos."""

    def reachable_from(
        self, graph: Graph, origin: str, *, trace: bool = False
    ) -> ReachabilityResult:
        graph.require_node(origin)  # NodeNotFoundError si el origen no existe
        hops: dict[str, int] = {origin: 0}
        queue: deque[str] = deque([origin])
        steps: list[TraceStep] = []
        if trace:
            steps.append(TraceStep(0, "enqueue", origin, {"hops": 0}))

        step = 0
        while queue:
            step += 1
            current = queue.popleft()
            if trace:
                steps.append(TraceStep(step, "visit", current, {"hops": hops[current]}))
            for arc in graph.neighbors(current):
                if arc.target in hops:  # se marca al encolar: no se encola dos veces
                    continue
                hops[arc.target] = hops[current] + 1
                queue.append(arc.target)
                if trace:
                    steps.append(
                        TraceStep(
                            step,
                            "enqueue",
                            arc.target,
                            {"hops": hops[arc.target], "from": current},
                        )
                    )
        return ReachabilityResult(origin=origin, hops=hops, trace=tuple(steps))
