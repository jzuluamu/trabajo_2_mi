#!/bin/sh
# Harness de calidad del servicio. Debe terminar en verde para considerar una tarea "hecha".
set -eu

echo "==> ruff (lint)";        ruff check src tests alembic
echo "==> ruff (formato)";     ruff format --check src tests alembic
echo "==> mypy (tipos)";       mypy
echo "==> bandit (seguridad)"; bandit -q -r src
echo "==> pip-audit (CVEs)"
uv export --frozen --no-hashes --no-emit-project --format requirements-txt -o /tmp/requirements.txt >/dev/null
pip-audit --requirement /tmp/requirements.txt --no-deps --disable-pip --progress-spinner off
echo "==> pytest";             pytest
