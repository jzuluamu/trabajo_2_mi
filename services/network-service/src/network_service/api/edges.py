"""Endpoints de conexiones — IMPLEMENTA: carril F1-C (docs/features/F1C-api-rest.md).

El router ya está registrado en `main.py`; F1-C solo agrega endpoints aquí.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from network_service.api.dependencies import (
    provide_delete_edge,
    provide_list_edges,
    provide_register_edge,
)
from network_service.api.schemas import EdgeIn, EdgeOut
from network_service.application.use_cases import DeleteEdge, ListEdges, RegisterEdge
from network_service.core.security import Role, require_roles

router = APIRouter(prefix="/api/v1/edges", tags=["edges"])


@router.post(
    "",
    response_model=EdgeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una conexión",
    dependencies=[Depends(require_roles(Role.COORDINATOR))],
)
def register_edge(
    payload: EdgeIn,
    use_case: Annotated[RegisterEdge, Depends(provide_register_edge)],
) -> EdgeOut:
    return EdgeOut.from_domain(use_case.execute(payload.to_domain()))


@router.get(
    "",
    response_model=list[EdgeOut],
    summary="Listar conexiones",
    dependencies=[Depends(require_roles(Role.COORDINATOR, Role.OPERATOR))],
)
def list_edges(use_case: Annotated[ListEdges, Depends(provide_list_edges)]) -> list[EdgeOut]:
    return [EdgeOut.from_domain(edge) for edge in use_case.execute()]


@router.delete(
    "/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una conexión",
    response_class=Response,
    dependencies=[Depends(require_roles(Role.COORDINATOR))],
)
def delete_edge(
    edge_id: str,
    use_case: Annotated[DeleteEdge, Depends(provide_delete_edge)],
) -> Response:
    use_case.execute(edge_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
