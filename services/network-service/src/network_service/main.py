"""Punto de entrada de network-service (Feature 1 — Red de cobertura)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from network_service.api import auth, edges, health, network, nodes
from network_service.api.error_mapping import register_domain_error_handler
from network_service.config import get_settings
from network_service.core.errors import register_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()  # falla al arrancar si la configuración es inválida
    logging.basicConfig(level=settings.log_level.upper())
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ServicioCerca · network-service",
        version="0.1.0",
        description="Registro y consulta de la red de cobertura (bases, zonas y trayectos).",
        lifespan=lifespan,
    )
    register_error_handlers(app)
    register_domain_error_handler(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    # Routers de F1 (carril F1-C): ya registrados; F1-C solo agrega endpoints en cada módulo.
    app.include_router(nodes.router)
    app.include_router(edges.router)
    app.include_router(network.router)
    return app


app = create_app()
