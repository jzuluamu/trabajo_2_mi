"""Interfaz mínima de F1 en la consola (AppTest + network-service falso con MockTransport)."""

import base64
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from console.clients.http import HttpServiceClient
from console.graph_view import DRAFT_ID, graph_payload
from tests.fake_network import FakeNetworkService

APP_PATH = str(Path(__file__).parents[1] / "src" / "console" / "app.py")


def _use_fake(monkeypatch: pytest.MonkeyPatch, fake: FakeNetworkService) -> None:
    """Todo cliente HTTP de la consola habla con `fake` en lugar de la red real."""
    original_init = HttpServiceClient.__init__

    def init(self: HttpServiceClient, base_url: str, **kwargs: Any) -> None:
        kwargs["transport"] = fake.transport
        original_init(self, base_url, **kwargs)

    monkeypatch.setattr(HttpServiceClient, "__init__", init)


@pytest.fixture
def coordinator(monkeypatch: pytest.MonkeyPatch) -> FakeNetworkService:
    fake = FakeNetworkService("coordinator")
    _use_fake(monkeypatch, fake)
    return fake


def _logged_in(role_key: str = "coordinator-key-123456") -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    at.sidebar.text_input(key="api_key_input").input(role_key)
    at.sidebar.button[0].click().run()
    return at


def _shown(elements: Any, text: str) -> bool:
    return any(element.value == text for element in elements)


def _table(at: AppTest, column: str) -> list[dict[str, Any]]:
    """Filas de la primera tabla que tiene la columna `column`."""
    for frame in at.dataframe:
        if column in frame.value.columns:
            records: list[dict[str, Any]] = frame.value.to_dict("records")
            return records
    raise AssertionError(f"no hay tabla con la columna {column!r}")


def _graph(at: AppTest, index: int = -1) -> str:
    """HTML del grafo embebido como URL data: (el coordinador ve dos: Red y Configurar)."""
    src = str(at.get("iframe")[index].proto.src)
    prefix = "data:text/html;base64,"
    assert src.startswith(prefix)
    return base64.b64decode(src[len(prefix) :]).decode("utf-8")


def _choose(at: AppTest, action: str) -> None:
    at.radio(key="admin_action").set_value(action).run()


# --- ambos roles: ver la red ------------------------------------------------------------


def test_operator_sees_network_tables_without_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fake(monkeypatch, FakeNetworkService("operator"))

    at = _logged_in("operator-key-1234567")

    assert not at.exception
    assert len(at.tabs) == 0
    assert _table(at, "Tipo")[0] == {
        "ID": "B_NORTE",
        "Tipo": "Base",
        "Nombre": "Base Norte",
        "Técnicos": "Ana (T01) ✔, Luis (T02) ✘",
    }
    assert _table(at, "Sentido") == [
        {
            "ID": "E01",
            "Origen": "B_NORTE",
            "Destino": "Z_CENTRO",
            "Minutos": 30.0,
            "Sentido": "↔ ambos sentidos",
        }
    ]
    assert not [b for b in at.button if b.key == "submit_node"]


def test_operator_sees_graph_kpis_and_card(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fake(monkeypatch, FakeNetworkService("operator"))

    at = _logged_in("operator-key-1234567")

    payload = graph_payload(_graph(at))
    assert [node["id"] for node in payload["nodes"]] == ["B_NORTE", "Z_CENTRO"]
    assert payload["selected"] == "B_NORTE"
    assert [(m.label, m.value) for m in at.metric] == [
        ("Bases", "1"),
        ("Zonas", "1"),
        ("Trayectos", "1"),
        ("Zonas sin conexión", "0"),
    ]
    assert _shown(at.markdown, ":green-badge[Disponible]")
    assert _table(at, "Trayecto") == [{"Trayecto": "↔ Centro", "Minutos": 30.0, "Conexión": "E01"}]


def test_selecting_a_zone_updates_card_and_graph_focus(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fake(monkeypatch, FakeNetworkService("operator"))
    at = _logged_in("operator-key-1234567")

    at.selectbox(key="card_node").set_value("Z_CENTRO").run()

    assert _shown(at.markdown, "#### Centro · Zona")
    assert graph_payload(_graph(at))["selected"] == "Z_CENTRO"


def test_refresh_button_reads_the_network_again(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    reads = coordinator.requests.count(("GET", "/api/v1/network"))

    at.button(key="refresh_network").click().run()

    assert coordinator.requests.count(("GET", "/api/v1/network")) > reads


def test_empty_network_shows_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fake(monkeypatch, FakeNetworkService("operator", empty=True))

    at = _logged_in("operator-key-1234567")

    assert any("La red está vacía" in info.value for info in at.info)
    assert len(at.dataframe) == 0


def test_network_unavailable_shows_readable_error(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    coordinator.down = True

    at.run()

    assert not at.exception
    assert any("No fue posible contactar network-service" in e.value for e in at.error)


# --- coordinador: configurar la red -----------------------------------------------------


def test_coordinator_registers_a_base_with_technicians(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    _choose(at, "Registrar nodo")
    at.selectbox(key="node_type").set_value("BASE")
    at.text_input(key="node_id").input("B_ESTE")
    at.text_input(key="node_name").input("Base Este")
    at.text_area(key="node_technicians").input("T10; Sara; sí\nT11; Juan; no")

    at.button(key="submit_node").click().run()

    assert coordinator.nodes["B_ESTE"]["technicians"] == [
        {"id": "T10", "name": "Sara", "available": True},
        {"id": "T11", "name": "Juan", "available": False},
    ]
    assert _shown(at.success, "Nodo 'B_ESTE' registrado.")


def test_duplicate_node_shows_contract_message(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    _choose(at, "Registrar nodo")
    at.selectbox(key="node_type").set_value("ZONE")
    at.text_input(key="node_id").input("Z_CENTRO")
    at.text_input(key="node_name").input("Otra")

    at.button(key="submit_node").click().run()

    assert _shown(at.error, "Ya existe un nodo con id 'Z_CENTRO'.")


def test_zone_with_technicians_is_rejected_before_calling_the_api(
    coordinator: FakeNetworkService,
) -> None:
    at = _logged_in()
    _choose(at, "Registrar nodo")
    at.selectbox(key="node_type").set_value("ZONE")
    at.text_input(key="node_id").input("Z_NUEVA")
    at.text_input(key="node_name").input("Nueva")
    at.text_area(key="node_technicians").input("T10; Sara")

    at.button(key="submit_node").click().run()

    assert _shown(at.error, "Solo las bases pueden tener técnicos.")
    assert ("POST", "/api/v1/nodes") not in coordinator.requests


def test_coordinator_registers_an_edge(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    at.text_input(key="edge_id").input("E02")
    at.selectbox(key="edge_source").set_value("Z_CENTRO")
    at.selectbox(key="edge_target").set_value("B_NORTE")
    at.number_input(key="edge_weight").set_value(12.0)
    at.checkbox(key="edge_bidir").uncheck()

    at.button(key="submit_edge").click().run()

    assert coordinator.edges["E02"] == {
        "id": "E02",
        "source": "Z_CENTRO",
        "target": "B_NORTE",
        "weight": 12.0,
        "bidirectional": False,
    }
    assert _shown(at.success, "Conexión 'E02' registrada.")


def test_negative_weight_shows_invalid_weight_message(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    at.text_input(key="edge_id").input("E02")
    at.number_input(key="edge_weight").set_value(-5.0)

    at.button(key="submit_edge").click().run()

    assert _shown(
        at.error,
        ("El peso de la conexión 'E02' debe ser mayor que 0 y menor o igual a 1440 minutos."),
    )
    assert "E02" not in coordinator.edges


def test_edge_in_progress_is_drawn_as_preview(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    at.selectbox(key="edge_source").set_value("Z_CENTRO")
    at.selectbox(key="edge_target").set_value("B_NORTE")
    at.number_input(key="edge_weight").set_value(-5.0).run()

    draft = [e for e in graph_payload(_graph(at))["edges"] if e["id"] == DRAFT_ID]

    assert draft[0]["from"] == "Z_CENTRO"
    assert draft[0]["label"] == "revisar"
    assert any("El peso debe ser mayor que 0" in c.value for c in at.caption)
    assert coordinator.edges.keys() == {"E01"}


def test_edge_form_needs_nodes(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fake(monkeypatch, FakeNetworkService("coordinator", empty=True))
    at = _logged_in()
    at.text_input(key="edge_id").input("E02")

    at.button(key="submit_edge").click().run()

    assert _shown(at.error, "Registre al menos dos nodos antes de crear conexiones.")


def test_delete_node_in_use_then_edge_then_node(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    _choose(at, "Eliminar")
    at.selectbox(key="delete_node_id").set_value("Z_CENTRO")

    at.button(key="delete_node").click().run()

    assert _shown(at.error, "El nodo 'Z_CENTRO' tiene conexiones; elimínelas primero.")

    at.selectbox(key="delete_edge_id").set_value("E01")
    at.button(key="delete_edge").click().run()
    assert _shown(at.success, "Conexión 'E01' eliminada.")

    at.selectbox(key="delete_node_id").set_value("Z_CENTRO")
    at.button(key="delete_node").click().run()
    assert _shown(at.success, "Nodo 'Z_CENTRO' eliminado.")
    assert sorted(coordinator.nodes) == ["B_NORTE"]


def test_load_button_without_file_asks_for_one(coordinator: FakeNetworkService) -> None:
    at = _logged_in()
    _choose(at, "Cargar red")

    at.button(key="import_network").click().run()

    assert _shown(at.error, "Seleccione un archivo JSON.")


# --- importación (st.file_uploader no es manipulable desde AppTest) ---------------------


def _import_script(content: bytes, replace: bool) -> None:
    import streamlit as st

    from console.components.network_admin import import_file
    from console.components.network_view import FLASH_KEY
    from console.config import get_settings

    st.session_state.setdefault("api_key", "coordinator-key-123456")
    if FLASH_KEY in st.session_state:
        st.success(st.session_state.pop(FLASH_KEY))
    else:
        import_file(get_settings(), content, replace=replace)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"{no es json", "El archivo no es un JSON válido."),
        (b'{"nodes": []}', "El archivo debe tener las listas 'nodes' y 'edges'."),
        (
            b'{"nodes": [], "edges": [{"id": "E9", "source": "A", "target": "B", "weight": -1}]}',
            "Peso inválido. (archivo: conexión #1)",
        ),
    ],
)
def test_import_file_errors_are_readable(
    coordinator: FakeNetworkService, content: bytes, message: str
) -> None:
    at = AppTest.from_function(_import_script, args=(content, True), default_timeout=10).run()

    assert at.error[0].value == message


def test_import_file_replaces_network(coordinator: FakeNetworkService) -> None:
    content = b'{"nodes": [{"id": "Z_ISLA", "type": "ZONE", "name": "Isla"}], "edges": []}'

    at = AppTest.from_function(_import_script, args=(content, True), default_timeout=10).run()

    assert at.success[0].value == "Red cargada: 1 nodos y 0 conexiones."
    assert sorted(coordinator.nodes) == ["Z_ISLA"]
