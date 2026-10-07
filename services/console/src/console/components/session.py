"""Inicio de sesión por API key: el rol lo decide network-service (`/api/v1/auth/whoami`)."""

import streamlit as st

from console.clients.http import ApiClientError
from console.clients.network_client import NetworkClient
from console.config import Settings

ROLE_LABELS = {"coordinator": "Coordinador de operaciones", "operator": "Operador de atención"}
UI_ROLES = frozenset(ROLE_LABELS)


def current_role() -> str | None:
    role = st.session_state.get("role")
    return role if isinstance(role, str) else None


def current_api_key() -> str | None:
    api_key = st.session_state.get("api_key")
    return api_key if isinstance(api_key, str) else None


def session_network_client(settings: Settings) -> NetworkClient:
    """Cliente de network-service con la API key de la sesión (usar como context manager)."""
    return NetworkClient(
        str(settings.network_service_url),
        api_key=current_api_key(),
        timeout=settings.request_timeout_seconds,
    )


def _login(settings: Settings, api_key: str) -> None:
    with NetworkClient(
        str(settings.network_service_url),
        api_key=api_key,
        timeout=settings.request_timeout_seconds,
    ) as client:
        try:
            role = client.whoami()
        except ApiClientError as error:
            st.sidebar.error(error.message)
            return
    if role not in UI_ROLES:
        st.sidebar.error("Esta clave no corresponde a un usuario de la consola.")
        return
    st.session_state["role"] = role
    st.session_state["api_key"] = api_key


def _logout() -> None:
    st.session_state.pop("role", None)
    st.session_state.pop("api_key", None)


def render_session_sidebar(settings: Settings) -> None:
    st.sidebar.header("Sesión")
    role = current_role()
    if role:
        st.sidebar.success(f"Rol: {ROLE_LABELS[role]}")
        st.sidebar.button("Cerrar sesión", on_click=_logout)
        return
    api_key = st.sidebar.text_input("API key", type="password", key="api_key_input")
    if st.sidebar.button("Ingresar") and api_key:
        _login(settings, api_key)
        if current_role():
            st.rerun()
