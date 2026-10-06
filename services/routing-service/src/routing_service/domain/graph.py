"""Grafo dirigido y ponderado de la red de cobertura (modelo en docs/02-modelo-de-grafo.md).

Internamente todo es dirigido: una conexión bidireccional se expande en dos arcos.
"""

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

from routing_service.domain.errors import DuplicateNodeError, InvalidWeightError, NodeNotFoundError


class NodeType(StrEnum):
    BASE = "BASE"
    ZONE = "ZONE"


@dataclass(frozen=True)
class Technician:
    id: str
    name: str
    available: bool


@dataclass(frozen=True)
class Node:
    id: str
    type: NodeType
    name: str
    technicians: tuple[Technician, ...] = field(default=())

    @property
    def available_technicians(self) -> tuple[Technician, ...]:
        return tuple(t for t in self.technicians if t.available)


@dataclass(frozen=True)
class Arc:
    """Tramo recorrible de `source` a `target` con costo `weight` (minutos)."""

    edge_id: str
    source: str
    target: str
    weight: float


def validate_weight(weight: float, edge_id: str) -> None:
    if not math.isfinite(weight) or weight <= 0:
        raise InvalidWeightError(
            f"La conexión '{edge_id}' tiene un peso inválido ({weight}); debe ser positivo.",
            edge_id=edge_id,
            weight=weight,
        )


class Graph:
    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._adjacency: dict[str, list[Arc]] = {}

    def add_node(self, node: Node) -> None:
        if node.id in self._nodes:
            raise DuplicateNodeError(f"El nodo '{node.id}' ya existe.", node_id=node.id)
        self._nodes[node.id] = node
        self._adjacency[node.id] = []

    def add_edge(
        self, edge_id: str, source: str, target: str, weight: float, *, bidirectional: bool = True
    ) -> None:
        self.require_node(source)
        self.require_node(target)
        validate_weight(weight, edge_id)
        self._adjacency[source].append(Arc(edge_id, source, target, weight))
        if bidirectional:
            self._adjacency[target].append(Arc(edge_id, target, source, weight))

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def require_node(self, node_id: str) -> Node:
        try:
            return self._nodes[node_id]
        except KeyError:
            raise NodeNotFoundError(f"El nodo '{node_id}' no existe.", node_id=node_id) from None

    def nodes(self) -> tuple[Node, ...]:
        return tuple(self._nodes[node_id] for node_id in sorted(self._nodes))

    def neighbors(self, node_id: str) -> tuple[Arc, ...]:
        """Arcos salientes ordenados por destino: recorridos deterministas y trazas estables."""
        self.require_node(node_id)
        return tuple(sorted(self._adjacency[node_id], key=lambda arc: (arc.target, arc.edge_id)))

    def arcs(self) -> Iterable[Arc]:
        for node_id in sorted(self._adjacency):
            yield from self.neighbors(node_id)
