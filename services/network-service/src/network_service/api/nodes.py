"""Endpoints de nodos — IMPLEMENTA: carril F1-C (docs/features/F1C-api-rest.md).

El router ya está registrado en `main.py`; F1-C solo agrega endpoints aquí.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from network_service.api.dependencies import (
    provide_delete_node,
    provide_get_node,
    provide_list_nodes,
    provide_register_node,
)
from network_service.api.schemas import NodeIn, NodeOut
from network_service.application.use_cases import DeleteNode, GetNode, ListNodes, RegisterNode
from network_service.core.security import Role, require_roles

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


@router.post(
    "",
    response_model=NodeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nodo",
    dependencies=[Depends(require_roles(Role.COORDINATOR))],
)
def register_node(
    payload: NodeIn,
    use_case: Annotated[RegisterNode, Depends(provide_register_node)],
) -> NodeOut:
    return NodeOut.from_domain(use_case.execute(payload.to_domain()))


@router.get(
    "",
    response_model=list[NodeOut],
    summary="Listar nodos",
    dependencies=[Depends(require_roles(Role.COORDINATOR, Role.OPERATOR))],
)
def list_nodes(use_case: Annotated[ListNodes, Depends(provide_list_nodes)]) -> list[NodeOut]:
    return [NodeOut.from_domain(node) for node in use_case.execute()]


@router.get(
    "/{node_id}",
    response_model=NodeOut,
    summary="Consultar un nodo",
    dependencies=[Depends(require_roles(Role.COORDINATOR, Role.OPERATOR))],
)
def get_node(
    node_id: str,
    use_case: Annotated[GetNode, Depends(provide_get_node)],
) -> NodeOut:
    return NodeOut.from_domain(use_case.execute(node_id))


@router.delete(
    "/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un nodo",
    response_class=Response,
    dependencies=[Depends(require_roles(Role.COORDINATOR))],
)
def delete_node(
    node_id: str,
    use_case: Annotated[DeleteNode, Depends(provide_delete_node)],
) -> Response:
    use_case.execute(node_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
