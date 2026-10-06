#!/bin/sh
# Arranque del contenedor: aplica migraciones pendientes y levanta la API.
set -eu
alembic upgrade head
exec uvicorn network_service.main:app --host 0.0.0.0 --port 8001 --no-server-header
