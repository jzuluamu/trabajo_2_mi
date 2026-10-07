"""Sección **Red** (ambos roles): mapa interactivo, indicadores, ficha del nodo y tabla."""

import base64

import streamlit as st

from console.clients.http import ApiClientError
from console.components.session import session_network_client
from console.config import Settings
from console.graph_view import DraftEdge, graph_html
from console.network_format import (
    JsonDict,
    edge_rows,
    error_text,
    md_escape,
    network_kpis,
    node_card,
    node_rows,
)

FLASH_KEY = "flash_message"
GRAPH_HEIGHT = 560


def flash(message: str) -> None:
    """Guarda un mensaje de éxito para mostrarlo tras el `st.rerun()` que refresca la red."""
    st.session_state[FLASH_KEY] = message


def load_network(settings: Settings) -> JsonDict | None:
    """Lee la red; si falla, muestra el mensaje del contrato y devuelve None."""
    with session_network_client(settings) as client:
        try:
            return client.get_network()
        except ApiClientError as error:
            st.error(error_text(error))
            return None


def show_flash() -> None:
    """Muestra (una sola vez) el mensaje guardado por `flash`, visible desde cualquier pestaña."""
    message = st.session_state.pop(FLASH_KEY, None)
    if isinstance(message, str):
        st.success(message)


def render_graph(
    network: JsonDict, *, selected: str | None = None, draft: DraftEdge | None = None
) -> None:
    """Grafo pyvis en un iframe con origen opaco (URL `data:`), ver ADR 0006.

    Con un string HTML, `st.iframe` comparte el origen de la app; con `data:` el documento
    no puede leer ni tocar la página de Streamlit aunque algo lograra ejecutarse dentro.
    """
    html = graph_html(network, selected=selected, draft=draft, height=GRAPH_HEIGHT)
    encoded = base64.b64encode(html.encode("utf-8")).decode("ascii")
    st.iframe(f"data:text/html;base64,{encoded}", height=GRAPH_HEIGHT + 4)


def _render_kpis(network: JsonDict) -> None:
    for column, (value, label, help_text) in zip(st.columns(4), network_kpis(network), strict=True):
        with column.container(border=True):
            st.metric(label, value)
            st.caption(help_text)


def _render_card(network: JsonDict, node_id: str) -> None:
    card = node_card(network, node_id)
    if card is None:
        return
    with st.container(border=True):
        st.markdown(f"#### {md_escape(card['title'])}")
        st.caption(f"ID {card['id']}")
        if card["note"]:
            st.warning(card["note"])
        if card["is_base"]:
            st.markdown("**Técnicos**")
            for technician in card["technicians"]:
                name, state = st.columns([3, 2], vertical_alignment="center")
                name.text(technician["label"])
                if technician["available"]:
                    state.badge("Disponible", color="green")
                else:
                    state.badge("No disponible", color="gray")
        st.markdown(f"**Trayectos ({len(card['links'])})**")
        if card["links"]:
            st.dataframe(card["links"], hide_index=True, width="stretch")


def render_network(network: JsonDict) -> None:
    header, refresh = st.columns([4, 1])
    header.subheader("Red de cobertura")
    if refresh.button("Actualizar", key="refresh_network"):
        st.rerun()
    nodes = network.get("nodes", [])
    if not nodes:
        st.info("La red está vacía. El coordinador puede registrar nodos o cargar la red demo.")
        return
    _render_kpis(network)

    graph, side = st.columns([5, 2], gap="medium")
    ids = [node["id"] for node in nodes]
    names = {node["id"]: f"{node['name']} · {node['id']}" for node in nodes}
    with side:
        selected = st.selectbox("Ficha de", ids, format_func=names.__getitem__, key="card_node")
        _render_card(network, selected)
    with graph:
        render_graph(network, selected=selected)

    with st.expander("Ver como tabla (accesible)"):
        st.markdown(f"**Bases y zonas** ({len(nodes)})")
        st.dataframe(node_rows(network), hide_index=True, width="stretch")
        st.markdown(f"**Conexiones** ({len(network.get('edges', []))}) — minutos de traslado")
        if network.get("edges"):
            st.dataframe(edge_rows(network), hide_index=True, width="stretch")
