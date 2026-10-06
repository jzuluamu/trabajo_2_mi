"""Entorno de migraciones (base de F1). F1-B agrega revisiones en alembic/versions/.

URL: `sqlalchemy.url` si se definió programáticamente (pruebas), si no `DATABASE_URL` (Settings).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from network_service.infrastructure.orm import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    from network_service.config import get_settings

    return get_settings().database_url.get_secret_value()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
