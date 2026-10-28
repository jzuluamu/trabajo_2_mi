"""Pestaña Cobertura de F2 (AppTest + servicios falsos con MockTransport)."""

from pathlib import Path
from typing import Any

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from console.clients.http import ApiClientError, HttpServiceClient
from console.clients.routing_client import RoutingClient
from console.coverage_format import reachable_rows, trace_rows, unreachable_rows
from tests.fake_network import FakeNetworkService

APP_PATH = str(Path(__file__).parents[1] / "src" / "console" / "app.py")


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeNetworkService:
    service = FakeNetworkService("operator")
    original_init = HttpServiceClient.__init__

    def init(self: HttpServiceClient, base_url: str, **kwargs: Any) -> None:
        kwargs["transport"] = service.transport
        original_init(self, base_url, **kwargs)

    monkeypatch.setattr(HttpServiceClient, "__init__", init)
    return service


def _logged_in() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    at.sidebar.text_input(key="api_key_input").input("operator-key-1234567")
    at.sidebar.button[0].click().run()
    return at


def _query(at: AppTest) -> AppTest:
    return at.button(key="coverage_submit").click().run()


def test_coordinator_has_three_tabs(fake: FakeNetworkService) -> None:
    fake.role = "coordinator"

    at = _logged_in()

    assert [tab.label for tab in at.tabs] == ["Red", "Cobertura", "Configurar red"]


def test_nothing_is_queried_until_the_button_is_pressed(fake: FakeNetworkService) -> None:
    at = _logged_in()

    assert not at.exception
    assert fake.coverage_queries == []


def test_query_without_zone_lists_reachable_nodes(fake: FakeNetworkService) -> None:
    at = _query(_logged_in())

    assert not at.exception
    assert fake.coverage_queries == [{"base": "B_NORTE", "trace": "false"}]
    frame = next(f for f in at.dataframe if "Tramos" in f.value.columns)
    assert frame.value.to_dict("records") == [
        {"ID": "Z_CENTRO", "Nombre": "Centro", "Tipo": "Zona", "Tramos": 1}
    ]
    assert not [m for m in at.success if "cubierta" in m.value]


def test_covered_zone_is_reported_as_success(fake: FakeNetworkService) -> None:
    at = _logged_in()
    at.selectbox(key="coverage_zone").set_value("Z_CENTRO")

    at = _query(at)

    assert fake.coverage_queries[-1]["zone"] == "Z_CENTRO"
    assert [m.value for m in at.success if "cubierta" in m.value] == [
        "Z\\_CENTRO está cubierta desde B\\_NORTE \\(1 tramo\\)\\."
    ]


def test_uncovered_zone_is_a_warning_and_listed(fake: FakeNetworkService) -> None:
    fake.uncovered = {"Z_CENTRO"}
    at = _logged_in()
    at.selectbox(key="coverage_zone").set_value("Z_CENTRO")

    at = _query(at)

    assert not at.exception
    assert "no hay conexión" in at.warning[0].value
    assert any("Zonas sin cobertura" in m.value for m in at.markdown)
    assert any(list(f.value.columns) == ["ID", "Nombre"] for f in at.dataframe)


def test_trace_is_shown_on_demand(fake: FakeNetworkService) -> None:
    at = _logged_in()
    at.checkbox(key="coverage_trace").check()

    at = _query(at)

    assert fake.coverage_queries[-1]["trace"] == "true"
    assert [e.label for e in at.expander if "BFS" in e.label] == ["Traza del recorrido BFS"]
    assert any("Paso" in f.value.columns for f in at.dataframe)


def test_api_error_is_shown_in_spanish(fake: FakeNetworkService) -> None:
    at = _logged_in()
    fake.unknown_base = True

    at = _query(at)

    assert [e.value for e in at.error] == ["La base 'B_NORTE' no existe."]


def test_network_without_bases_shows_a_hint(fake: FakeNetworkService) -> None:
    fake.nodes.pop("B_NORTE")
    fake.edges.clear()

    at = _logged_in()

    assert not at.exception
    assert any("No hay bases registradas" in i.value for i in at.info)
    assert not [b for b in at.button if b.key == "coverage_submit"]


def test_base_without_connections_gets_a_hint(fake: FakeNetworkService) -> None:
    fake.uncovered = {"Z_CENTRO"}

    at = _query(_logged_in())

    assert not at.exception
    assert any("no tiene conexiones" in i.value for i in at.info)


# --- cliente y formateo -----------------------------------------------------------------


def test_client_sends_query_and_api_key() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"base": "B_NORTE"})

    transport = httpx.MockTransport(handler)
    with RoutingClient("http://routing-service:8002", api_key="k" * 16, transport=transport) as c:
        assert c.get_coverage("B_NORTE", "Z_CENTRO", trace=True) == {"base": "B_NORTE"}

    assert dict(seen[0].url.params) == {"base": "B_NORTE", "zone": "Z_CENTRO", "trace": "true"}
    assert seen[0].headers["X-API-Key"] == "k" * 16


def test_client_translates_api_errors() -> None:
    body = {"code": "INVALID_ORIGIN", "message": "No es una base.", "details": {}}
    transport = httpx.MockTransport(lambda _: httpx.Response(422, json=body))

    client = RoutingClient("http://routing-service:8002", transport=transport)
    with client, pytest.raises(ApiClientError) as error:
        client.get_coverage("Z_CENTRO")

    assert error.value.code == "INVALID_ORIGIN"


def test_row_formatters() -> None:
    network = {"nodes": [{"id": "Z1", "type": "ZONE", "name": "Uno"}]}
    report = {
        "reachable": [{"node_id": "Z1", "type": "ZONE", "hops": 2}],
        "unreachable_zones": ["Z9"],
        "trace": [{"step": 1, "action": "visit", "node": "Z1", "data": {"hops": 2, "from": "B"}}],
    }

    assert reachable_rows(network, report) == [
        {"ID": "Z1", "Nombre": "Uno", "Tipo": "Zona", "Tramos": 2}
    ]
    assert unreachable_rows(network, report) == [{"ID": "Z9", "Nombre": "Z9"}]
    assert trace_rows(report) == [
        {"Paso": 1, "Acción": "Visita", "Nodo": "Z1", "Tramos": 2, "Desde": "B"}
    ]
    assert trace_rows({"trace": None}) == []
