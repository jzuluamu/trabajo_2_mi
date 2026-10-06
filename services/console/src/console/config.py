"""Configuración de la consola. No guarda API keys: cada usuario ingresa la suya."""

from functools import lru_cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    network_service_url: HttpUrl
    routing_service_url: HttpUrl
    request_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()  # valores provienen del entorno
