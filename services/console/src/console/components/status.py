"""Panel de estado de los microservicios (endpoints `/health`, públicos)."""

import streamlit as st

from console.clients.http import ApiClientError, HttpServiceClient
from console.clients.network_client import NetworkClient
from console.clients.routing_client import RoutingClient
from console.config import Settings


def _service_clients(settings: Settings) -> list[HttpServiceClient]:
    timeout = settings.request_timeout_seconds
    return [
        NetworkClient(str(settings.network_service_url), timeout=timeout),
        RoutingClient(str(settings.routing_service_url), timeout=timeout),
    ]


def render_service_status(settings: Settings) -> None:
    st.subheader("Estado de los servicios")
    columns = st.columns(2)
    for column, client in zip(columns, _service_clients(settings), strict=True):
        with client, column:
            try:
                client.health()
            except ApiClientError as error:
                st.error(f"{client.service_name}: no disponible — {error.message}")
            else:
                st.success(f"{client.service_name}: operativo")
