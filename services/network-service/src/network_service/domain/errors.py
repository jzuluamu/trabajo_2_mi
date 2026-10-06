"""Errores de dominio de F1. Cada clase tiene un `code` estable del contrato (docs/03-api.md).

CONGELADO (base de F1). La API traduce `code` → HTTP en `api/error_mapping.py`.
`details` NUNCA debe incluir valores inválidos enviados por el cliente (solo campo, ids válidos,
índices); ver docs/06-seguridad.md.
"""

from typing import Any, ClassVar


class DomainError(Exception):
    code: ClassVar[str] = "DOMAIN_ERROR"

    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = dict(details)


class InvalidFieldError(DomainError):
    """Identificador, nombre o técnicos inválidos (formato o reglas de forma)."""

    code = "VALIDATION_ERROR"


class InvalidWeightError(DomainError):
    code = "INVALID_WEIGHT"


class SelfLoopError(DomainError):
    code = "SELF_LOOP"


class NodeNotFoundError(DomainError):
    code = "NODE_NOT_FOUND"


class EdgeNotFoundError(DomainError):
    code = "EDGE_NOT_FOUND"


class DuplicateIdError(DomainError):
    code = "DUPLICATE_ID"


class DuplicateEdgeError(DomainError):
    code = "DUPLICATE_EDGE"


class NodeInUseError(DomainError):
    code = "NODE_IN_USE"
