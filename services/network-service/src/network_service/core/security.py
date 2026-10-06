"""Autorización por rol mediante el encabezado `X-API-Key` (ver docs/06-seguridad.md)."""

import secrets
from collections.abc import Callable
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Security, status
from fastapi.security import APIKeyHeader

from network_service.config import Settings, get_settings
from network_service.core.errors import AppError

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class Role(StrEnum):
    COORDINATOR = "coordinator"
    OPERATOR = "operator"
    INTERNAL = "internal"


def resolve_role(api_key: str, settings: Settings) -> Role | None:
    """Devuelve el rol asociado a la clave; compara en tiempo constante."""
    candidates = (
        (Role.COORDINATOR, settings.coordinator_api_key),
        (Role.OPERATOR, settings.operator_api_key),
        (Role.INTERNAL, settings.internal_api_key),
    )
    matched: Role | None = None
    for role, secret in candidates:
        if secrets.compare_digest(api_key.encode(), secret.get_secret_value().encode()):
            matched = role
    return matched


def require_roles(*allowed: Role) -> Callable[..., Role]:
    """Dependencia FastAPI: exige una API key válida cuyo rol esté en `allowed`."""

    def dependency(
        api_key: Annotated[str | None, Security(API_KEY_HEADER)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> Role:
        if not api_key:
            raise AppError(
                "UNAUTHENTICATED", "Falta el encabezado X-API-Key.", status.HTTP_401_UNAUTHORIZED
            )
        role = resolve_role(api_key, settings)
        if role is None:
            raise AppError("UNAUTHENTICATED", "API key inválida.", status.HTTP_401_UNAUTHORIZED)
        if role not in allowed:
            raise AppError(
                "FORBIDDEN",
                f"El rol '{role}' no tiene permiso para esta acción.",
                status.HTTP_403_FORBIDDEN,
            )
        return role

    return dependency
