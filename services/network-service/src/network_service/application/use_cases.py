"""Casos de uso de F1 (SRP: uno por clase) — IMPLEMENTA: carril F1-A.

Las clases, constructores y firmas de `execute` están CONGELADOS: el carril F1-C (API) los
importa. Solo se reemplazan los cuerpos marcados con `NotImplementedError`.
Orden exacto de validaciones y errores: docs/features/F1A-dominio-casos-de-uso.md.
"""

from collections.abc import Sequence

from network_service.application.ports import NetworkReader, NetworkRepository
from network_service.domain.errors import (
    DomainError,
    DuplicateEdgeError,
    DuplicateIdError,
    EdgeNotFoundError,
    NodeInUseError,
    NodeNotFoundError,
)
from network_service.domain.models import Edge, ImportSummary, Network, Node
from network_service.domain.rules import edges_conflict, validate_edge, validate_node
from network_service.infrastructure.memory_repository import InMemoryNetworkRepository


class RegisterNode:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, node: Node) -> Node:
        """validate_node → DUPLICATE_ID (nodo) → DUPLICATE_ID (técnico) → guardar."""
        validate_node(node)
        if self._repository.get_node(node.id) is not None:
            raise DuplicateIdError(f"Ya existe un nodo con id '{node.id}'.", node_id=node.id)
        for technician in node.technicians:
            if self._repository.technician_exists(technician.id):
                raise DuplicateIdError(
                    f"Ya existe un técnico con id '{technician.id}'.",
                    technician_id=technician.id,
                )
        self._repository.add_node(node)
        return node


class RegisterEdge:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, edge: Edge) -> Edge:
        """validate_edge → DUPLICATE_ID → NODE_NOT_FOUND (source, luego target)
        → DUPLICATE_EDGE → guardar."""
        validate_edge(edge)
        if self._repository.get_edge(edge.id) is not None:
            raise DuplicateIdError(f"Ya existe una conexión con id '{edge.id}'.", edge_id=edge.id)
        if self._repository.get_node(edge.source) is None:
            raise NodeNotFoundError(f"El nodo '{edge.source}' no existe.", node_id=edge.source)
        if self._repository.get_node(edge.target) is None:
            raise NodeNotFoundError(f"El nodo '{edge.target}' no existe.", node_id=edge.target)
        for existing in self._repository.list_edges():
            if edges_conflict(edge, existing):
                raise DuplicateEdgeError(
                    f"Ya existe una conexión entre '{existing.source}' y "
                    f"'{existing.target}' ({existing.id}).",
                    edge_id=existing.id,
                )
        self._repository.add_edge(edge)
        return edge


class GetNode:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self, node_id: str) -> Node:
        """Devuelve el nodo o lanza NODE_NOT_FOUND."""
        node = self._repository.get_node(node_id)
        if node is None:
            raise NodeNotFoundError(f"El nodo '{node_id}' no existe.", node_id=node_id)
        return node


class ListNodes:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self) -> list[Node]:
        """Nodos ordenados por id."""
        return self._repository.list_nodes()


class ListEdges:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self) -> list[Edge]:
        """Conexiones ordenadas por id."""
        return self._repository.list_edges()


class DeleteNode:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, node_id: str) -> None:
        """NODE_NOT_FOUND → NODE_IN_USE (si una conexión lo usa como source o target) → borrar."""
        if self._repository.get_node(node_id) is None:
            raise NodeNotFoundError(f"El nodo '{node_id}' no existe.", node_id=node_id)
        uses = sorted(
            edge.id
            for edge in self._repository.list_edges()
            if node_id in (edge.source, edge.target)
        )
        if uses:
            raise NodeInUseError(
                f"El nodo '{node_id}' tiene conexiones; elimínelas primero.",
                node_id=node_id,
                edge_ids=uses,
            )
        self._repository.delete_node(node_id)


class DeleteEdge:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, edge_id: str) -> None:
        """EDGE_NOT_FOUND → borrar."""
        if self._repository.get_edge(edge_id) is None:
            raise EdgeNotFoundError(f"La conexión '{edge_id}' no existe.", edge_id=edge_id)
        self._repository.delete_edge(edge_id)


class GetNetwork:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self) -> Network:
        """Red completa con nodos y conexiones ordenados por id."""
        return Network(
            nodes=tuple(self._repository.list_nodes()),
            edges=tuple(self._repository.list_edges()),
        )


class ImportNetwork:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(
        self, nodes: Sequence[Node], edges: Sequence[Edge], *, replace: bool
    ) -> ImportSummary:
        """Importación atómica (todo o nada).

        Valida TODO antes de escribir (mismas reglas que RegisterNode/RegisterEdge, aplicadas en
        orden: primero nodos, luego conexiones) sobre el estado de partida (vacío si `replace`,
        actual si no). Ante el primer error, lo relanza agregando a `details`
        `{"section": "nodes"|"edges", "index": i}` y NO escribe nada. Si todo es válido, persiste
        con `repository.save_network(nodes, edges, replace=replace)`.
        """
        scratch = InMemoryNetworkRepository()
        if not replace:
            scratch.save_network(
                self._repository.list_nodes(), self._repository.list_edges(), replace=True
            )
        for index, node in enumerate(nodes):
            try:
                RegisterNode(scratch).execute(node)
            except DomainError as error:
                error.details["section"] = "nodes"
                error.details["index"] = index
                raise
        for index, edge in enumerate(edges):
            try:
                RegisterEdge(scratch).execute(edge)
            except DomainError as error:
                error.details["section"] = "edges"
                error.details["index"] = index
                raise
        self._repository.save_network(nodes, edges, replace=replace)
        return ImportSummary(nodes=len(nodes), edges=len(edges))
