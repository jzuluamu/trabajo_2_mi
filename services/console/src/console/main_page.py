"""Página principal de la consola (lógica importable y medible por cobertura)."""

import streamlit as st

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
    st.info(
        "Fase 0: la red, la cobertura y la ruta de menor costo se habilitan en las Fases 1 y 2 "
        "(ver docs/09-fases-y-roadmap.md)."
    )
