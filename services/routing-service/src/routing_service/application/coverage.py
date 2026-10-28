"""Caso de uso de Feature 2: ¿qué zonas puede cubrir una base? (docs/04-algoritmos-bfs.md)."""

from dataclasses import dataclass

from routing_service.application.ports import NetworkGateway
from routing_service.domain.errors import (
    InvalidOriginError,
    OriginNotFoundError,
    ZoneNotFoundError,
)
from routing_service.domain.graph import NodeType
from routing_service.domain.results import TraceStep
from routing_service.domain.strategies import ReachabilityStrategy


@dataclass(frozen=True)
class ReachableNode:
    node_id: str
    type: NodeType
    hops: int


@dataclass(frozen=True)
class ZoneCoverage:
    id: str
    covered: bool
    hops: int | None
    message: str


@dataclass(frozen=True)
class CoverageReport:
    base: str
    reachable: tuple[ReachableNode, ...]
    unreachable_zones: tuple[str, ...]
    zone: ZoneCoverage | None
    trace: tuple[TraceStep, ...]


def _hops_label(hops: int) -> str:
    return f"{hops} tramo" if hops == 1 else f"{hops} tramos"


class CheckCoverage:
    def __init__(self, gateway: NetworkGateway, strategy: ReachabilityStrategy) -> None:
        self._gateway = gateway
        self._strategy = strategy

    def execute(self, base: str, zone: str | None = None, *, trace: bool = False) -> CoverageReport:
        graph = self._gateway.load_graph()

        if not graph.has_node(base):
            raise OriginNotFoundError(f"La base '{base}' no existe.", node_id=base)
        if graph.require_node(base).type is not NodeType.BASE:
            raise InvalidOriginError(
                f"'{base}' no es una base; la cobertura se consulta desde una base.", node_id=base
            )
        if zone is not None and (
            not graph.has_node(zone) or graph.require_node(zone).type is not NodeType.ZONE
        ):
            raise ZoneNotFoundError(f"La zona '{zone}' no existe.", node_id=zone)

        result = self._strategy.reachable_from(graph, base, trace=trace)

        reachable = tuple(
            sorted(
                (
                    ReachableNode(node.id, node.type, result.hops[node.id])
                    for node in graph.nodes()
                    if node.id != base and result.reaches(node.id)
                ),
                key=lambda item: (item.hops, item.node_id),
            )
        )
        unreachable = tuple(
            node.id
            for node in graph.nodes()
            if node.type is NodeType.ZONE and not result.reaches(node.id)
        )
        return CoverageReport(
            base=base,
            reachable=reachable,
            unreachable_zones=unreachable,
            zone=self._zone_coverage(base, zone, result.hops) if zone is not None else None,
            trace=result.trace if trace else (),
        )

    @staticmethod
    def _zone_coverage(base: str, zone: str, hops: dict[str, int]) -> ZoneCoverage:
        if zone in hops:
            return ZoneCoverage(
                zone,
                True,
                hops[zone],
                f"{zone} está cubierta desde {base} ({_hops_label(hops[zone])}).",
            )
        return ZoneCoverage(
            zone, False, None, f"{zone} no está cubierta: no hay conexión desde {base}."
        )
