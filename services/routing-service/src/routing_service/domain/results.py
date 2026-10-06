"""Resultados inmutables que devuelven los algoritmos (contrato entre dominio y API)."""

from dataclasses import dataclass, field
from typing import Any


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
    """Camino de menor costo; `found=False` cuando el destino no es alcanzable."""

    origin: str
    destination: str
    found: bool
    path: tuple[str, ...] = ()
    total_cost: float | None = None
    trace: tuple[TraceStep, ...] = ()

    @property
    def hops(self) -> int | None:
        return len(self.path) - 1 if self.found else None
