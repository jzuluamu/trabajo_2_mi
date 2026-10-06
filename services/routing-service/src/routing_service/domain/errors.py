"""Errores de dominio. La capa API los traduce a códigos HTTP (docs/03-api.md)."""


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, **details: object) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NodeNotFoundError(DomainError):
    code = "NODE_NOT_FOUND"


class DuplicateNodeError(DomainError):
    code = "DUPLICATE_ID"


class InvalidWeightError(DomainError):
    code = "INVALID_WEIGHT"
