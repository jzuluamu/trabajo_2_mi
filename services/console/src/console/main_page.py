"""Página principal de la consola (lógica importable y medible por cobertura)."""

import streamlit as st

from console.components.network_admin import render_network_admin
from console.components.network_view import load_network, render_network, show_flash
from console.components.session import ROLE_LABELS, current_role, render_session_sidebar
from console.components.status import render_service_status
from console.config import get_settings


def main() -> None:
    st.set_page_config(page_title="ServicioCerca · Consola", layout="wide")
    settings = get_settings()

    st.title("ServicioCerca · Consola de operación")
    st.caption("Cobertura de bases y alternativa de atención de menor costo.")
    render_session_sidebar(settings)
    render_service_status(settings)

    role = current_role()
    if role is None:
        st.info("Ingrese su API key en la barra lateral para usar la consola.")
        return
    st.write(f"Sesión iniciada como **{ROLE_LABELS[role]}**.")

    network = load_network(settings)
    if network is None:
        return
    show_flash()
    if role != "coordinator":
        render_network(network)
        return
    view_tab, admin_tab = st.tabs(["Red", "Configurar red"])
    with view_tab:
        render_network(network)
    with admin_tab:
        render_network_admin(settings, network)
