"""Sección **Configurar red** (solo coordinador): registrar, borrar y cargar la red demo.

Cada acción llama a network-service; los errores se muestran con el `message` del contrato
(p. ej. `INVALID_WEIGHT` con peso negativo). Tras un éxito se refresca la página con `flash`.
"""

from collections.abc import Callable

import streamlit as st

from console.clients.http import ApiClientError
from console.clients.network_client import NetworkClient
from console.components.network_view import flash
from console.components.session import session_network_client
from console.config import Settings
from console.network_format import (
    TYPE_LABELS,
    FormInputError,
    JsonDict,
    edge_payload,
    error_text,
    node_payload,
    parse_network_file,
)


def _run(settings: Settings, action: Callable[[NetworkClient], object], success: str) -> None:
    """Ejecuta `action` con el cliente de la sesión; éxito → flash + rerun, error → st.error."""
    with session_network_client(settings) as client:
        try:
            action(client)
        except ApiClientError as error:
            st.error(error_text(error))
            return
    flash(success)
    st.rerun()


def _node_form(settings: Settings) -> None:
    with st.form("create_node", clear_on_submit=False):
        st.markdown("**Registrar base o zona**")
        node_type = st.selectbox(
            "Tipo", list(TYPE_LABELS), format_func=TYPE_LABELS.__getitem__, key="node_type"
        )
        node_id = st.text_input("ID (A-Z, 0-9, '_' o '-')", key="node_id")
        name = st.text_input("Nombre", key="node_name")
        technicians = st.text_area(
            "Técnicos (solo bases): una línea por técnico, 'ID; Nombre; sí/no'",
            key="node_technicians",
            placeholder="T10; Sara; sí\nT11; Juan; no",
        )
        if not st.form_submit_button("Registrar nodo", key="submit_node"):
            return
    try:
        payload = node_payload(node_id, node_type, name, technicians)
    except FormInputError as error:
        st.error(str(error))
        return
    _run(settings, lambda c: c.create_node(payload), f"Nodo '{payload['id']}' registrado.")


def _edge_form(settings: Settings, node_ids: list[str]) -> None:
    with st.form("create_edge", clear_on_submit=False):
        st.markdown("**Registrar conexión**")
        edge_id = st.text_input("ID de la conexión", key="edge_id")
        source = st.selectbox("Origen", node_ids, key="edge_source")
        target = st.selectbox("Destino", node_ids, key="edge_target")
        weight = st.number_input("Minutos de traslado", value=10.0, step=1.0, key="edge_weight")
        bidirectional = st.checkbox("Se recorre en ambos sentidos", value=True, key="edge_bidir")
        if not st.form_submit_button("Registrar conexión", key="submit_edge"):
            return
    if source is None or target is None:
        st.error("Registre al menos dos nodos antes de crear conexiones.")
        return
    payload = edge_payload(edge_id, source, target, float(weight), bidirectional)
    _run(settings, lambda c: c.create_edge(payload), f"Conexión '{payload['id']}' registrada.")


def _delete_controls(settings: Settings, node_ids: list[str], edge_ids: list[str]) -> None:
    st.markdown("**Eliminar**")
    node_column, edge_column = st.columns(2)
    node_id = node_column.selectbox("Nodo", node_ids, key="delete_node_id")
    if node_column.button("Eliminar nodo", key="delete_node") and node_id:
        _run(settings, lambda c: c.delete_node(node_id), f"Nodo '{node_id}' eliminado.")
    edge_id = edge_column.selectbox("Conexión", edge_ids, key="delete_edge_id")
    if edge_column.button("Eliminar conexión", key="delete_edge") and edge_id:
        _run(settings, lambda c: c.delete_edge(edge_id), f"Conexión '{edge_id}' eliminada.")


def _import_controls(settings: Settings) -> None:
    st.markdown("**Cargar red demo** (`seed/red_demo.json` u otro JSON con `nodes` y `edges`)")
    uploaded = st.file_uploader("Archivo JSON", type=["json"], key="import_file")
    replace = st.checkbox("Reemplazar la red actual", value=True, key="import_replace")
    if not st.button("Cargar red", key="import_network"):
        return
    if uploaded is None:
        st.error("Seleccione un archivo JSON.")
        return
    import_file(settings, uploaded.getvalue(), replace=replace)


def import_file(settings: Settings, content: bytes, *, replace: bool) -> None:
    try:
        payload = parse_network_file(content, replace=replace)
    except FormInputError as error:
        st.error(str(error))
        return
    nodes, edges = len(payload["nodes"]), len(payload["edges"])
    _run(
        settings,
        lambda c: c.import_network(payload),
        f"Red cargada: {nodes} nodos y {edges} conexiones.",
    )


def render_network_admin(settings: Settings, network: JsonDict) -> None:
    node_ids = [node["id"] for node in network.get("nodes", [])]
    edge_ids = [edge["id"] for edge in network.get("edges", [])]
    left, right = st.columns(2)
    with left:
        _node_form(settings)
    with right:
        _edge_form(settings, node_ids)
    st.divider()
    _delete_controls(settings, node_ids, edge_ids)
    st.divider()
    _import_controls(settings)
