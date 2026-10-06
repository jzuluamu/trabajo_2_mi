import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from network_service.api.error_mapping import STATUS_BY_CODE, register_domain_error_handler
from network_service.core.errors import register_error_handlers
from network_service.domain.errors import (
    DomainError,
    DuplicateEdgeError,
    DuplicateIdError,
    EdgeNotFoundError,
    InvalidFieldError,
    InvalidWeightError,
    NodeInUseError,
    NodeNotFoundError,
    SelfLoopError,
)

EXPECTED = [
    (InvalidFieldError, 422, "VALIDATION_ERROR"),
    (InvalidWeightError, 422, "INVALID_WEIGHT"),
    (SelfLoopError, 422, "SELF_LOOP"),
    (NodeNotFoundError, 404, "NODE_NOT_FOUND"),
    (EdgeNotFoundError, 404, "EDGE_NOT_FOUND"),
    (DuplicateIdError, 409, "DUPLICATE_ID"),
    (DuplicateEdgeError, 409, "DUPLICATE_EDGE"),
    (NodeInUseError, 409, "NODE_IN_USE"),
]


def _client_raising(error: DomainError) -> TestClient:
    app = FastAPI()
    register_error_handlers(app)
    register_domain_error_handler(app)

    @app.get("/raise")
    def _raise() -> None:
        raise error

    return TestClient(app)


@pytest.mark.parametrize(("error_class", "status", "code"), EXPECTED)
def test_domain_errors_map_to_contract_status(
    error_class: type[DomainError], status: int, code: str
) -> None:
    response = _client_raising(error_class("Mensaje legible.", node_id="Z1")).get("/raise")

    assert response.status_code == status
    assert response.json() == {
        "code": code,
        "message": "Mensaje legible.",
        "details": {"node_id": "Z1"},
    }


def test_every_domain_error_code_has_a_status() -> None:
    assert {code for _, _, code in EXPECTED} == set(STATUS_BY_CODE)


def test_unknown_domain_error_falls_back_to_400() -> None:
    response = _client_raising(DomainError("Otro error.")).get("/raise")

    assert response.status_code == 400
    assert response.json()["code"] == "DOMAIN_ERROR"
