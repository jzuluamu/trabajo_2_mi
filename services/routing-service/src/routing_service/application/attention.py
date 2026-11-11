"""Caso de uso de mejor atención — IMPLEMENTA: carril F3-B (docs/features/F3-sesiones.md).

Los dataclasses, la clase, el constructor y la firma de `execute` están CONGELADOS (base de F3):
el carril F3-C (API) los importa. F3-B reemplaza solo el cuerpo de `execute` y puede agregar
funciones privadas de apoyo en este archivo.
"""

from dataclasses import dataclass

from routing_service.application.ports import NetworkGateway
from routing_service.domain.errors import ZoneNotFoundError
from routing_service.domain.graph import Node, NodeType
from routing_service.domain.results import PathResult, TraceStep
from routing_service.domain.strategies import PathFinder


@dataclass(frozen=True)
class AvailableTechnician:
    id: str
    name: str


@dataclass(frozen=True)
class BestBase:
    base: str
    technicians: tuple[AvailableTechnician, ...]
    path: tuple[str, ...]
    total_cost: float
    hops: int


@dataclass(frozen=True)
class AlternativeBase:
    base: str
    total_cost: float
    hops: int


@dataclass(frozen=True)
class AttentionReport:
    zone: str
    found: bool
    best: BestBase | None
    alternatives: tuple[AlternativeBase, ...]
    message: str
    trace: tuple[TraceStep, ...]


def _minutes(value: float) -> str:
    return f"{value:g} min"


def _cost_and_hops(result: PathResult) -> tuple[float, int]:
    """Costo y tramos de un camino hallado; un `PathFinder` que no los informa viola su contrato."""
    if not result.found or result.total_cost is None or result.hops is None:
        raise RuntimeError("Un PathFinder devolvió un camino hallado sin costo o sin tramos.")
    return result.total_cost, result.hops


def _ranking_key(item: tuple[Node, PathResult]) -> tuple[float, int, str]:
    base, result = item
    cost, hops = _cost_and_hops(result)
    return cost, hops, base.id


def _tag_with_base(steps: tuple[TraceStep, ...], base: str) -> tuple[TraceStep, ...]:
    return tuple(TraceStep(s.step, s.action, s.node, {**s.data, "base": base}) for s in steps)


def _unattended_message(zone: str, bases_without_technicians: list[str]) -> str:
    if bases_without_technicians:
        return (
            f"{zone} no se puede atender: solo es alcanzable desde bases sin técnicos "
            f"disponibles ({', '.join(bases_without_technicians)})."
        )
    return f"{zone} no se puede atender: es inalcanzable desde toda base."


class FindBestAttention:
    """Entre las bases con técnico disponible, la de menor costo hasta la zona."""

    def __init__(self, gateway: NetworkGateway, path_finder: PathFinder) -> None:
        self._gateway = gateway
        self._path_finder = path_finder

    def execute(self, zone: str, *, trace: bool = False) -> AttentionReport:
        graph = self._gateway.load_graph()

        if not graph.has_node(zone) or graph.require_node(zone).type is not NodeType.ZONE:
            raise ZoneNotFoundError(f"La zona '{zone}' no existe.", node_id=zone)

        bases = [node for node in graph.nodes() if node.type is NodeType.BASE]
        candidates = [base for base in bases if base.available_technicians]

        reached: list[tuple[Node, PathResult]] = []
        steps: list[TraceStep] = []
        for base in candidates:
            result = self._path_finder.find(graph, base.id, zone, trace=trace)
            if trace:
                steps.extend(_tag_with_base(result.trace, base.id))
            if result.found:
                reached.append((base, result))

        if not reached:
            without_technicians = [
                base.id
                for base in bases
                if not base.available_technicians
                and self._path_finder.find(graph, base.id, zone).found
            ]
            return AttentionReport(
                zone=zone,
                found=False,
                best=None,
                alternatives=(),
                message=_unattended_message(zone, without_technicians),
                trace=tuple(steps),
            )

        reached.sort(key=_ranking_key)
        (best_base, best_result), others = reached[0], reached[1:]
        best_cost, best_hops = _cost_and_hops(best_result)
        technicians = tuple(
            AvailableTechnician(t.id, t.name) for t in best_base.available_technicians
        )
        names = ", ".join(t.name for t in technicians)
        alternatives = tuple(
            AlternativeBase(base.id, *_cost_and_hops(result)) for base, result in others
        )
        return AttentionReport(
            zone=zone,
            found=True,
            best=BestBase(best_base.id, technicians, best_result.path, best_cost, best_hops),
            alternatives=alternatives,
            message=f"Atender desde {best_base.id} ({names}): {_minutes(best_cost)}.",
            trace=tuple(steps),
        )
