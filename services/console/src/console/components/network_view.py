"""Sección **Red** (ambos roles): tablas de nodos y conexiones leídas de `GET /api/v1/network`."""

import streamlit as st

from console.clients.http import ApiClientError
from console.components.session import session_network_client
from console.config import Settings
from console.network_format import JsonDict, edge_rows, error_text, node_rows

FLASH_KEY = "flash_message"


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


def render_network(network: JsonDict) -> None:
    header, refresh = st.columns([4, 1])
    header.subheader("Red de cobertura")
    if refresh.button("Actualizar", key="refresh_network"):
        st.rerun()

    nodes, edges = node_rows(network), edge_rows(network)
    st.markdown(f"**Bases y zonas** ({len(nodes)})")
    if nodes:
        st.dataframe(nodes, hide_index=True, width="stretch")
    else:
        st.info("La red está vacía. El coordinador puede registrar nodos o cargar la red demo.")
    st.markdown(f"**Conexiones** ({len(edges)}) — peso en minutos de traslado")
    if edges:
        st.dataframe(edges, hide_index=True, width="stretch")
