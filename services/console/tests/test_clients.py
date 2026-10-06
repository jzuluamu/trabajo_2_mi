import httpx
import pytest

from console.clients.http import ApiClientError
from console.clients.network_client import NetworkClient
from console.clients.routing_client import RoutingClient


def _client(handler: httpx.MockTransport, api_key: str | None = None) -> NetworkClient:
    return NetworkClient("http://network-service:8001", api_key=api_key, transport=handler)


def test_health_returns_body() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"status": "ok"}))

    with RoutingClient("http://routing-service:8002", transport=transport) as client:
        assert client.health() == {"status": "ok"}


def test_api_key_is_sent_in_header() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers.get("X-API-Key")
        return httpx.Response(200, json={"role": "operator"})

    with _client(httpx.MockTransport(handler), api_key="secret-operator-key") as client:
        assert client.whoami() == "operator"
    assert seen["key"] == "secret-operator-key"


def test_api_error_body_is_translated() -> None:
    body = {"code": "UNAUTHENTICATED", "message": "API key inválida.", "details": {"a": 1}}
    transport = httpx.MockTransport(lambda _: httpx.Response(401, json=body))

    with _client(transport) as client, pytest.raises(ApiClientError) as error:
        client.whoami()

    assert (error.value.code, error.value.message) == ("UNAUTHENTICATED", "API key inválida.")
    assert (error.value.status_code, error.value.details) == (401, {"a": 1})


@pytest.mark.parametrize(
    "response",
    [httpx.Response(502, text="Bad gateway"), httpx.Response(500, json=["no", "dict"])],
)
def test_unexpected_error_body_has_generic_message(response: httpx.Response) -> None:
    transport = httpx.MockTransport(lambda _: response)

    with _client(transport) as client, pytest.raises(ApiClientError) as error:
        client.health()

    assert error.value.code == f"HTTP_{response.status_code}"
    assert error.value.message == "Respuesta inesperada del servicio."


def test_connection_failure_is_service_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with _client(httpx.MockTransport(handler)) as client, pytest.raises(ApiClientError) as error:
        client.health()

    assert error.value.code == "SERVICE_UNAVAILABLE"
    assert "network-service" in error.value.message
