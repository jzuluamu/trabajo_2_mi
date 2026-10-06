"""Repositorio en memoria: implementación de REFERENCIA del puerto `NetworkRepository`.

Se usa en pruebas (F1-A, F1-C) y como repositorio por defecto hasta que F1-B active PostgreSQL.
Cumple `tests/contract/repository_contract.py`. CONGELADO (base de F1).
"""

from collections.abc import Sequence
from threading import Lock

from network_service.domain.errors import DuplicateIdError
from network_service.domain.models import Edge, Node


class InMemoryNetworkRepository:
    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}
        self._lock = Lock()

    # --- lectura -------------------------------------------------------------------------
    def get_node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def list_nodes(self) -> list[Node]:
        return [self._nodes[node_id] for node_id in sorted(self._nodes)]

    def get_edge(self, edge_id: str) -> Edge | None:
        return self._edges.get(edge_id)

    def list_edges(self) -> list[Edge]:
        return [self._edges[edge_id] for edge_id in sorted(self._edges)]

    def technician_exists(self, technician_id: str) -> bool:
        return any(t.id == technician_id for n in self._nodes.values() for t in n.technicians)

    # --- escritura -----------------------------------------------------------------------
    def add_node(self, node: Node) -> None:
        with self._lock:
            self._insert_nodes(self._nodes, [node])

    def delete_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.pop(node_id, None)

    def add_edge(self, edge: Edge) -> None:
        with self._lock:
            self._insert_edges(self._edges, [edge])

    def delete_edge(self, edge_id: str) -> None:
        with self._lock:
            self._edges.pop(edge_id, None)

    def save_network(self, nodes: Sequence[Node], edges: Sequence[Edge], *, replace: bool) -> None:
        with self._lock:
            # Se trabaja sobre copias y se publica al final: atomicidad (todo o nada).
            new_nodes: dict[str, Node] = {} if replace else dict(self._nodes)
            new_edges: dict[str, Edge] = {} if replace else dict(self._edges)
            self._insert_nodes(new_nodes, nodes)
            self._insert_edges(new_edges, edges)
            self._nodes, self._edges = new_nodes, new_edges

    # --- apoyo ---------------------------------------------------------------------------
    @staticmethod
    def _insert_nodes(target: dict[str, Node], nodes: Sequence[Node]) -> None:
        technician_ids = {t.id for n in target.values() for t in n.technicians}
        for node in nodes:
            if node.id in target:
                raise DuplicateIdError(f"Ya existe un nodo con id '{node.id}'.", node_id=node.id)
            for technician in node.technicians:
                if technician.id in technician_ids:
                    raise DuplicateIdError(
                        f"Ya existe un técnico con id '{technician.id}'.",
                        technician_id=technician.id,
                    )
                technician_ids.add(technician.id)
            target[node.id] = node

    @staticmethod
    def _insert_edges(target: dict[str, Edge], edges: Sequence[Edge]) -> None:
        for edge in edges:
            if edge.id in target:
                raise DuplicateIdError(
                    f"Ya existe una conexión con id '{edge.id}'.", edge_id=edge.id
                )
            target[edge.id] = edge
