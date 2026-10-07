"""Endpoints de la red e importación — IMPLEMENTA: carril F1-C (docs/features/F1C-api-rest.md).

El router ya está registrado en `main.py`; F1-C solo agrega endpoints aquí.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from network_service.api.dependencies import provide_get_network, provide_import_network
from network_service.api.schemas import ImportSummaryOut, NetworkImportIn, NetworkOut
from network_service.application.use_cases import GetNetwork, ImportNetwork
from network_service.core.security import Role, require_roles

router = APIRouter(prefix="/api/v1/network", tags=["network"])


@router.get(
    "",
    response_model=NetworkOut,
    summary="Consultar la red completa",
    dependencies=[Depends(require_roles(Role.COORDINATOR, Role.OPERATOR, Role.INTERNAL))],
)
def get_network(use_case: Annotated[GetNetwork, Depends(provide_get_network)]) -> NetworkOut:
    return NetworkOut.from_domain(use_case.execute())


@router.post(
    "/import",
    response_model=ImportSummaryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Importar la red",
    dependencies=[Depends(require_roles(Role.COORDINATOR))],
)
def import_network(
    payload: NetworkImportIn,
    use_case: Annotated[ImportNetwork, Depends(provide_import_network)],
) -> ImportSummaryOut:
    summary = use_case.execute(
        [node.to_domain() for node in payload.nodes],
        [edge.to_domain() for edge in payload.edges],
        replace=payload.replace,
    )
    return ImportSummaryOut.from_domain(summary)
