"""Casos de uso de F1 (SRP: uno por clase) — IMPLEMENTA: carril F1-A.

Las clases, constructores y firmas de `execute` están CONGELADOS: el carril F1-C (API) los
importa. Solo se reemplazan los cuerpos marcados con `NotImplementedError`.
Orden exacto de validaciones y errores: docs/features/F1A-dominio-casos-de-uso.md.
"""

from collections.abc import Sequence

from network_service.application.ports import NetworkReader, NetworkRepository
from network_service.domain.models import Edge, ImportSummary, Network, Node


class RegisterNode:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, node: Node) -> Node:
        """validate_node → DUPLICATE_ID (nodo) → DUPLICATE_ID (técnico) → guardar."""
        raise NotImplementedError("F1-A")


class RegisterEdge:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, edge: Edge) -> Edge:
        """validate_edge → DUPLICATE_ID → NODE_NOT_FOUND (source, luego target)
        → DUPLICATE_EDGE → guardar."""
        raise NotImplementedError("F1-A")


class GetNode:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self, node_id: str) -> Node:
        """Devuelve el nodo o lanza NODE_NOT_FOUND."""
        raise NotImplementedError("F1-A")


class ListNodes:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self) -> list[Node]:
        """Nodos ordenados por id."""
        raise NotImplementedError("F1-A")


class ListEdges:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self) -> list[Edge]:
        """Conexiones ordenadas por id."""
        raise NotImplementedError("F1-A")


class DeleteNode:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, node_id: str) -> None:
        """NODE_NOT_FOUND → NODE_IN_USE (si una conexión lo usa como source o target) → borrar."""
        raise NotImplementedError("F1-A")


class DeleteEdge:
    def __init__(self, repository: NetworkRepository) -> None:
        self._repository = repository

    def execute(self, edge_id: str) -> None:
        """EDGE_NOT_FOUND → borrar."""
        raise NotImplementedError("F1-A")


class GetNetwork:
    def __init__(self, repository: NetworkReader) -> None:
        self._repository = repository

    def execute(self) -> Network:
        """Red completa con nodos y conexiones ordenados por id."""
        raise NotImplementedError("F1-A")


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
        raise NotImplementedError("F1-A")
