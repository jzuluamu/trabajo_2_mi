"""Mapeo común de errores de dominio al formato HTTP del contrato."""

from fastapi import status

from routing_service.core.errors import AppError
from routing_service.domain.errors import DomainError

STATUS_BY_CODE = {
    "ORIGIN_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "DESTINATION_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "ZONE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "INVALID_ORIGIN": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "INVALID_WEIGHT": status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def to_app_error(exc: DomainError) -> AppError:
    return AppError(
        exc.code,
        exc.message,
        STATUS_BY_CODE.get(exc.code, status.HTTP_400_BAD_REQUEST),
        exc.details,
    )
