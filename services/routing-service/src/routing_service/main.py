"""Punto de entrada de routing-service (Features 2 y 3)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from routing_service.api import health
from routing_service.config import get_settings
from routing_service.core.errors import register_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()  # falla al arrancar si la configuración es inválida
    logging.basicConfig(level=settings.log_level.upper())
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ServicioCerca · routing-service",
        version="0.1.0",
        description="Cobertura (BFS) y alternativa de atención de menor costo (Dijkstra).",
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.include_router(health.router)
    return app


app = create_app()
