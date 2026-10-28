"""Sección **Cobertura** (ambos roles): qué zonas alcanza una base (F2, BFS)."""

import streamlit as st

from console.clients.http import ApiClientError
from console.components.session import session_routing_client
from console.config import Settings
from console.coverage_format import (
    nodes_of_type,
    reachable_rows,
    trace_rows,
    unreachable_rows,
)
from console.network_format import JsonDict, error_text, md_escape

NO_ZONE = ""


def _render_zone(zone: JsonDict) -> None:
    message = md_escape(zone["message"])
    if zone["covered"]:
        st.success(message)
    else:
        st.warning(message)


def _render_report(network: JsonDict, report: JsonDict) -> None:
    if report["zone"]:
        _render_zone(report["zone"])
    reached, missing = st.columns(2)
    with reached.container(border=True):
        st.metric("Nodos alcanzables", len(report["reachable"]))
        st.caption("Sin contar la base de origen.")
    with missing.container(border=True):
        st.metric("Zonas sin cobertura", len(report["unreachable_zones"]))
        st.caption("No hay camino desde la base elegida.")

    st.markdown("**Alcanzables desde la base** — tramos mínimos")
    if report["reachable"]:
        st.dataframe(reachable_rows(network, report), hide_index=True, width="stretch")
    else:
        st.info("Esta base no tiene conexiones hacia ninguna zona.")
    if report["unreachable_zones"]:
        st.markdown("**Zonas sin cobertura**")
        st.dataframe(unreachable_rows(network, report), hide_index=True, width="stretch")
    if report.get("trace"):
        with st.expander("Traza del recorrido BFS"):
            st.dataframe(trace_rows(report), hide_index=True, width="stretch")


def render_coverage(settings: Settings, network: JsonDict) -> None:
    st.subheader("Consulta de cobertura")
    st.caption(
        "Una zona está cubierta si existe un camino desde la base siguiendo las conexiones "
        "(recorrido en anchura, BFS). Se informa el mínimo de tramos, no el costo."
    )
    bases = nodes_of_type(network, "BASE")
    if not bases:
        st.info("No hay bases registradas. El coordinador puede cargar la red demo.")
        return
    zones = nodes_of_type(network, "ZONE")
    names = {node["id"]: f"{node['name']} · {node['id']}" for node in network["nodes"]}

    base = st.selectbox(
        "Base", [node["id"] for node in bases], format_func=names.__getitem__, key="coverage_base"
    )
    zone = st.selectbox(
        "Zona a verificar (opcional)",
        [NO_ZONE, *(node["id"] for node in zones)],
        format_func=lambda zone_id: names.get(zone_id, "— Todas —"),
        key="coverage_zone",
    )
    with_trace = st.checkbox("Mostrar traza paso a paso", key="coverage_trace")
    if not st.button("Consultar cobertura", key="coverage_submit", type="primary"):
        return

    with session_routing_client(settings) as client:
        try:
            report = client.get_coverage(base, zone or None, trace=with_trace)
        except ApiClientError as error:
            st.error(error_text(error))
            return
    _render_report(network, report)
