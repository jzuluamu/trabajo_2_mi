"""Configuración del servicio, leída de variables de entorno (ver `.env.example`)."""

from functools import lru_cache

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_API_KEY_LENGTH = 16
PLACEHOLDER_PREFIX = "CHANGE_ME"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: SecretStr
    coordinator_api_key: SecretStr
    operator_api_key: SecretStr
    internal_api_key: SecretStr
    log_level: str = "INFO"

    @field_validator("coordinator_api_key", "operator_api_key", "internal_api_key")
    @classmethod
    def _api_key_is_strong(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if raw.startswith(PLACEHOLDER_PREFIX):
            raise ValueError("la API key conserva el valor de ejemplo; ejecute `make env`")
        if len(raw) < MIN_API_KEY_LENGTH:
            raise ValueError(f"la API key debe tener al menos {MIN_API_KEY_LENGTH} caracteres")
        return value

    @model_validator(mode="after")
    def _api_keys_are_distinct(self) -> "Settings":
        keys = {
            self.coordinator_api_key.get_secret_value(),
            self.operator_api_key.get_secret_value(),
            self.internal_api_key.get_secret_value(),
        }
        if len(keys) != 3:
            raise ValueError("cada rol debe tener una API key distinta")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # valores provienen del entorno
