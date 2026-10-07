"""Inyección de dependencias (DIP). DUEÑO: carril F1-C (agrega los proveedores de casos de uso).

`get_repository` es de la base y está CONGELADO: devuelve una única instancia por proceso,
construida por `infrastructure/factory.py` (F1-B decide si es memoria o PostgreSQL).
En pruebas se reemplaza con `app.dependency_overrides[get_repository]`.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from network_service.application.ports import NetworkRepository
from network_service.application.use_cases import (
    DeleteEdge,
    DeleteNode,
    GetNetwork,
    GetNode,
    ImportNetwork,
    ListEdges,
    ListNodes,
    RegisterEdge,
    RegisterNode,
)
from network_service.config import get_settings
from network_service.infrastructure.factory import build_repository


@lru_cache
def _repository_singleton() -> NetworkRepository:
    return build_repository(get_settings())


def get_repository() -> NetworkRepository:
    return _repository_singleton()


def provide_register_node(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> RegisterNode:
    return RegisterNode(repository)


def provide_get_node(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> GetNode:
    return GetNode(repository)


def provide_list_nodes(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> ListNodes:
    return ListNodes(repository)


def provide_delete_node(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> DeleteNode:
    return DeleteNode(repository)


def provide_register_edge(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> RegisterEdge:
    return RegisterEdge(repository)


def provide_list_edges(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> ListEdges:
    return ListEdges(repository)


def provide_delete_edge(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> DeleteEdge:
    return DeleteEdge(repository)


def provide_get_network(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> GetNetwork:
    return GetNetwork(repository)


def provide_import_network(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> ImportNetwork:
    return ImportNetwork(repository)
