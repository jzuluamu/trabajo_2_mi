from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from console.clients.http import ApiClientError, HttpServiceClient
from console.clients.network_client import NetworkClient

APP_PATH = str(Path(__file__).parents[1] / "src" / "console" / "app.py")


def _healthy(self: HttpServiceClient) -> dict[str, Any]:
    return {"status": "ok"}


def _down(self: HttpServiceClient) -> dict[str, Any]:
    raise ApiClientError("SERVICE_UNAVAILABLE", f"No fue posible contactar {self.service_name}.")


def _app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=10).run()


def test_shows_services_up_and_asks_for_login(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HttpServiceClient, "health", _healthy)

    at = _app()

    assert not at.exception
    assert at.title[0].value == "ServicioCerca · Consola de operación"
    assert [s.value for s in at.success] == [
        "network-service: operativo",
        "routing-service: operativo",
    ]
    assert "Ingrese su API key" in at.info[0].value


def test_shows_readable_message_when_services_are_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HttpServiceClient, "health", _down)

    at = _app()

    assert not at.exception
    assert len(at.error) == 2
    assert "network-service: no disponible" in at.error[0].value


def test_operator_logs_in_and_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HttpServiceClient, "health", _healthy)
    monkeypatch.setattr(NetworkClient, "whoami", lambda self: "operator")
    at = _app()

    at.sidebar.text_input(key="api_key_input").input("operator-key-123456")
    at.sidebar.button[0].click().run()

    assert at.session_state["role"] == "operator"
    assert at.sidebar.success[0].value == "Rol: Operador de atención"

    at.sidebar.button[0].click().run()

    assert "role" not in at.session_state


def test_invalid_key_shows_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject(self: NetworkClient) -> str:
        raise ApiClientError("UNAUTHENTICATED", "API key inválida.", 401)

    monkeypatch.setattr(HttpServiceClient, "health", _healthy)
    monkeypatch.setattr(NetworkClient, "whoami", reject)
    at = _app()

    at.sidebar.text_input(key="api_key_input").input("bad-key-1234567890")
    at.sidebar.button[0].click().run()

    assert "role" not in at.session_state
    assert at.sidebar.error[0].value == "API key inválida."


def test_internal_key_is_not_a_console_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HttpServiceClient, "health", _healthy)
    monkeypatch.setattr(NetworkClient, "whoami", lambda self: "internal")
    at = _app()

    at.sidebar.text_input(key="api_key_input").input("internal-key-1234567")
    at.sidebar.button[0].click().run()

    assert "role" not in at.session_state
    assert "no corresponde" in at.sidebar.error[0].value
