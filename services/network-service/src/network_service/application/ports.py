"""Puertos de persistencia (ISP + DIP). CONGELADO (base de F1).

- Los casos de uso (F1-A) dependen de estos `Protocol`, nunca de una implementación concreta.
- Implementaciones: `InMemoryNetworkRepository` (base, referencia) y el repositorio
  SQLAlchemy (F1-B).
- El comportamiento exigido está fijado por `tests/contract/repository_contract.py` (LSP): toda
  implementación debe pasar esa suite.

Reglas del contrato del repositorio:
- No valida reglas de negocio (eso es F1-A); solo almacena y consulta.
- Listados ordenados por `id` ascendente; un nodo se devuelve con sus técnicos en el orden guardado.
- Insertar un id existente (nodo, conexión o técnico) lanza `DuplicateIdError`.
- `delete_*` de un id inexistente no hace nada. Borrar un nodo borra sus técnicos.
- `save_network` es atómico: si falla, el estado previo queda intacto.
"""

from collections.abc import Sequence
from typing import Protocol

from network_service.domain.models import Edge, Node


class NetworkReader(Protocol):
    def get_node(self, node_id: str) -> Node | None: ...

    def list_nodes(self) -> list[Node]: ...

    def get_edge(self, edge_id: str) -> Edge | None: ...

    def list_edges(self) -> list[Edge]: ...

    def technician_exists(self, technician_id: str) -> bool: ...


class NetworkWriter(Protocol):
    def add_node(self, node: Node) -> None: ...

    def delete_node(self, node_id: str) -> None: ...

    def add_edge(self, edge: Edge) -> None: ...

    def delete_edge(self, edge_id: str) -> None: ...

    def save_network(
        self, nodes: Sequence[Node], edges: Sequence[Edge], *, replace: bool
    ) -> None: ...


class NetworkRepository(NetworkReader, NetworkWriter, Protocol):
    """Lectura + escritura. routing-service (vía API) solo necesita lectura."""
