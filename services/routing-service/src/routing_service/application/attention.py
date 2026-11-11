"""Caso de uso de mejor atención — IMPLEMENTA: carril F3-B (docs/features/F3-sesiones.md).

Los dataclasses, la clase, el constructor y la firma de `execute` están CONGELADOS (base de F3):
el carril F3-C (API) los importa. F3-B reemplaza solo el cuerpo de `execute` y puede agregar
funciones privadas de apoyo en este archivo.
"""

from dataclasses import dataclass

from routing_service.application.ports import NetworkGateway
from routing_service.domain.results import TraceStep
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


class FindBestAttention:
    """Entre las bases con técnico disponible, la de menor costo hasta la zona."""

    def __init__(self, gateway: NetworkGateway, path_finder: PathFinder) -> None:
        self._gateway = gateway
        self._path_finder = path_finder

    def execute(self, zone: str, *, trace: bool = False) -> AttentionReport:
        raise NotImplementedError("F3-B: implementar FindBestAttention")
