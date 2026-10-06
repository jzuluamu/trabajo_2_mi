from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from routing_service.core.errors import AppError, register_error_handlers


class _Payload(BaseModel):
    weight: float = Field(gt=0)


def _app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/validate")
    def validate(payload: _Payload) -> dict[str, float]:
        return {"weight": payload.weight}

    @app.get("/domain-error")
    def domain_error() -> None:
        raise AppError("NODE_NOT_FOUND", "La zona 'Z9' no existe.", 404, {"node_id": "Z9"})

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secreto interno")

    return app


def test_validation_errors_use_standard_format_without_echoing_input() -> None:
    response = TestClient(_app()).post("/validate", json={"weight": -5})

    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "VALIDATION_ERROR"
    assert body["details"]["errors"][0]["field"] == "body.weight"
    assert "-5" not in response.text


def test_app_error_is_serialized() -> None:
    response = TestClient(_app()).get("/domain-error")

    assert response.status_code == 404
    assert response.json() == {
        "code": "NODE_NOT_FOUND",
        "message": "La zona 'Z9' no existe.",
        "details": {"node_id": "Z9"},
    }


def test_unknown_route_uses_standard_format() -> None:
    response = TestClient(_app()).get("/no-existe")

    assert response.status_code == 404
    assert response.json()["code"] == "HTTP_404"


def test_unexpected_errors_do_not_leak_internals() -> None:
    response = TestClient(_app(), raise_server_exceptions=False).get("/boom")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert "secreto" not in response.text
