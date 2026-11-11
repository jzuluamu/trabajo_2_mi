"""Resultados inmutables que devuelven los algoritmos (contrato entre dominio y API)."""

from dataclasses import dataclass, field
from typing import Any

from routing_service.domain.graph import Arc


@dataclass(frozen=True)
class TraceStep:
    """Paso de la traza: `action` es p. ej. 'visit', 'enqueue', 'relax', 'skip'."""

    step: int
    action: str
    node: str | None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReachabilityResult:
    """Alcance desde `origin`: `hops[n]` = número mínimo de tramos hasta `n`."""

    origin: str
    hops: dict[str, int]
    trace: tuple[TraceStep, ...] = ()

    def reaches(self, node_id: str) -> bool:
        return node_id in self.hops


@dataclass(frozen=True)
class PathResult:
    """Camino hallado por un `PathFinder`; `found=False` cuando el destino no es alcanzable.

    `legs` son los arcos recorridos en orden (`legs[i]` va de `path[i]` a `path[i + 1]`).
    """

    origin: str
    destination: str
    found: bool
    path: tuple[str, ...] = ()
    total_cost: float | None = None
    trace: tuple[TraceStep, ...] = ()
    legs: tuple[Arc, ...] = ()

    @property
    def hops(self) -> int | None:
        return len(self.path) - 1 if self.found else None
