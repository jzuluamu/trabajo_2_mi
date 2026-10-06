"""Entidades del dominio de la red de cobertura (docs/02-modelo-de-grafo.md).

CONGELADO (base de F1): cambiarlo requiere PR revisado por los dueños de F1-A, F1-B y F1-C.
Las entidades son inmutables y NO se validan solas: las reglas viven en `domain/rules.py` (F1-A).
"""

from dataclasses import dataclass
from enum import StrEnum

ID_PATTERN = r"^[A-Z0-9_-]{1,32}$"
NAME_MAX_LENGTH = 80
WEIGHT_MAX_MINUTES = 1440.0


class NodeType(StrEnum):
    BASE = "BASE"
    ZONE = "ZONE"


@dataclass(frozen=True, slots=True)
class Technician:
    id: str
    name: str
    available: bool = True


@dataclass(frozen=True, slots=True)
class Node:
    """Base (con técnicos) o zona. `technicians` solo puede tener elementos si `type` es BASE."""

    id: str
    type: NodeType
    name: str
    technicians: tuple[Technician, ...] = ()


@dataclass(frozen=True, slots=True)
class Edge:
    """Trayecto `source`→`target` de `weight` minutos; `bidirectional` lo hace recorrible en ambos
    sentidos con el mismo peso."""

    id: str
    source: str
    target: str
    weight: float
    bidirectional: bool = True


@dataclass(frozen=True, slots=True)
class Network:
    """Red completa; `nodes` y `edges` ordenados por `id`."""

    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True, slots=True)
class ImportSummary:
    nodes: int
    edges: int
