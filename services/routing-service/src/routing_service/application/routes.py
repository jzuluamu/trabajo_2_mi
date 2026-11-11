"""Caso de uso de ruta de menor costo — IMPLEMENTA: carril F3-B (docs/features/F3-sesiones.md).

Los dataclasses, la clase, el constructor y la firma de `execute` están CONGELADOS (base de F3):
el carril F3-C (API) los importa. F3-B reemplaza solo el cuerpo de `execute` y puede agregar
funciones privadas de apoyo en este archivo.
"""

from dataclasses import dataclass

from routing_service.application.ports import NetworkGateway
from routing_service.domain.results import TraceStep
from routing_service.domain.strategies import PathFinder


@dataclass(frozen=True)
class Leg:
    edge_id: str
    source: str
    target: str
    weight: float


@dataclass(frozen=True)
class FewestHops:
    path: tuple[str, ...]
    hops: int
    cost: float


@dataclass(frozen=True)
class RouteReport:
    found: bool
    origin: str
    destination: str
    path: tuple[str, ...]
    total_cost: float | None
    hops: int | None
    legs: tuple[Leg, ...]
    fewest_hops: FewestHops | None
    message: str
    trace: tuple[TraceStep, ...]


class FindCheapestRoute:
    """Ruta de menor costo (`path_finder`) comparada con la de menos tramos."""

    def __init__(
        self, gateway: NetworkGateway, path_finder: PathFinder, fewest_hops_finder: PathFinder
    ) -> None:
        self._gateway = gateway
        self._path_finder = path_finder
        self._fewest_hops_finder = fewest_hops_finder

    def execute(self, origin: str, destination: str, *, trace: bool = False) -> RouteReport:
        raise NotImplementedError("F3-B: implementar FindCheapestRoute")
