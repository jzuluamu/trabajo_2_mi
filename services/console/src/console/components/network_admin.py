"""Sección **Configurar red** (solo coordinador): registrar, borrar y cargar la red demo.

A la izquierda, el mapa con la conexión en edición dibujada como vista previa; a la derecha,
la acción elegida. Cada acción llama a network-service, que es quien valida: los errores se
muestran con el `message` del contrato (p. ej. `INVALID_WEIGHT`). Tras un éxito se refresca
la página con `flash`.
"""

from collections.abc import Callable

import streamlit as st

from console.clients.http import ApiClientError
from console.clients.network_client import NetworkClient
from console.components.network_view import flash, render_graph
from console.components.session import session_network_client
from console.config import Settings
from console.graph_view import DraftEdge
from console.network_format import (
    TYPE_LABELS,
    WEIGHT_MAX_MINUTES,
    FormInputError,
    JsonDict,
    edge_payload,
    error_text,
    node_payload,
    parse_network_file,
)

ACTIONS = ("Registrar conexión", "Registrar nodo", "Eliminar", "Cargar red")


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
        if not st.form_submit_button("Registrar nodo", key="submit_node", type="primary"):
            return
    try:
        payload = node_payload(node_id, node_type, name, technicians)
    except FormInputError as error:
        st.error(str(error))
        return
    _run(settings, lambda c: c.create_node(payload), f"Nodo '{payload['id']}' registrado.")


def _edge_form(settings: Settings, node_ids: list[str], labels: dict[str, str]) -> DraftEdge | None:
    """Campos sin `st.form` para que el mapa dibuje la conexión mientras se escribe."""
    edge_id = st.text_input("ID de la conexión", key="edge_id", placeholder="E10")
    source_column, target_column = st.columns(2)
    source = source_column.selectbox(
        "Desde", node_ids, format_func=labels.__getitem__, key="edge_source"
    )
    target = target_column.selectbox(
        "Hasta",
        node_ids,
        index=min(1, len(node_ids) - 1) if node_ids else None,
        format_func=labels.__getitem__,
        key="edge_target",
    )
    weight = st.number_input("Minutos de traslado", value=10.0, step=1.0, key="edge_weight")
    bidirectional = st.checkbox("Se recorre en ambos sentidos", value=True, key="edge_bidir")
    draft = None
    if source is not None and target is not None and source != target:
        in_range = 0 < weight <= WEIGHT_MAX_MINUTES
        draft = DraftEdge(source, target, float(weight), bidirectional, valid=in_range)
        if not in_range:
            st.caption(
                f":orange[El peso debe ser mayor que 0 y como máximo "
                f"{int(WEIGHT_MAX_MINUTES)} minutos.]"
            )
    if not st.button("Registrar conexión", key="submit_edge", type="primary"):
        return draft
    if source is None or target is None:
        st.error("Registre al menos dos nodos antes de crear conexiones.")
        return draft
    payload = edge_payload(edge_id, source, target, float(weight), bidirectional)
    _run(settings, lambda c: c.create_edge(payload), f"Conexión '{payload['id']}' registrada.")
    return draft


def _delete_controls(
    settings: Settings, node_ids: list[str], edge_ids: list[str], labels: dict[str, str]
) -> None:
    st.caption("Un nodo con trayectos no se puede borrar: elimine antes sus conexiones.")
    node_column, edge_column = st.columns(2)
    node_id = node_column.selectbox(
        "Nodo", node_ids, format_func=labels.__getitem__, key="delete_node_id"
    )
    if node_column.button("Eliminar nodo", key="delete_node") and node_id:
        _run(settings, lambda c: c.delete_node(node_id), f"Nodo '{node_id}' eliminado.")
    edge_id = edge_column.selectbox("Conexión", edge_ids, key="delete_edge_id")
    if edge_column.button("Eliminar conexión", key="delete_edge") and edge_id:
        _run(settings, lambda c: c.delete_edge(edge_id), f"Conexión '{edge_id}' eliminada.")


def _import_controls(settings: Settings) -> None:
    st.caption("`seed/red_demo.json` u otro JSON con las listas `nodes` y `edges`.")
    uploaded = st.file_uploader("Archivo JSON", type=["json"], key="import_file")
    replace = st.checkbox("Reemplazar la red actual", value=True, key="import_replace")
    if replace:
        st.caption(":orange[Se borra todo lo registrado y queda solo lo del archivo.]")
    if not st.button("Cargar red", key="import_network", type="primary"):
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
    nodes = network.get("nodes", [])
    node_ids = [node["id"] for node in nodes]
    edge_ids = [edge["id"] for edge in network.get("edges", [])]
    labels = {node["id"]: f"{node['name']} · {node['id']}" for node in nodes}
    graph, panel = st.columns([5, 3], gap="medium")
    draft = None
    with panel, st.container(border=True):
        action = st.radio("¿Qué desea hacer?", ACTIONS, key="admin_action", horizontal=True)
        if action == "Registrar conexión":
            draft = _edge_form(settings, node_ids, labels)
        elif action == "Registrar nodo":
            _node_form(settings)
        elif action == "Eliminar":
            _delete_controls(settings, node_ids, edge_ids, labels)
        else:
            _import_controls(settings)
    with graph:
        st.caption("Lo que escribe se dibuja en el mapa antes de guardarlo (línea punteada).")
        render_graph(network, draft=draft)
