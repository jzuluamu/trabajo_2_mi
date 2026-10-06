"""Traducción de errores de dominio a respuestas HTTP del contrato. CONGELADO (base de F1).

Los routers (F1-C) NO capturan `DomainError`: lo dejan propagar y este manejador responde
`{code, message, details}` con el estado HTTP de `STATUS_BY_CODE`.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from network_service.core.errors import error_response
from network_service.domain.errors import DomainError

STATUS_BY_CODE: dict[str, int] = {
    "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "INVALID_WEIGHT": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "SELF_LOOP": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "NODE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "EDGE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "DUPLICATE_ID": status.HTTP_409_CONFLICT,
    "DUPLICATE_EDGE": status.HTTP_409_CONFLICT,
    "NODE_IN_USE": status.HTTP_409_CONFLICT,
}


def register_domain_error_handler(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        status_code = STATUS_BY_CODE.get(exc.code, status.HTTP_400_BAD_REQUEST)
        return error_response(status_code, exc.code, exc.message, exc.details)
