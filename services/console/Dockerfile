# syntax=docker/dockerfile:1
# Etapas: base -> deps (solo runtime) -> runtime | test (con herramientas de calidad)
FROM python:3.12.8-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONPATH=/app/src \
    PATH=/opt/venv/bin:$PATH
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv
RUN groupadd --system app && useradd --system --gid app --home-dir /app app
WORKDIR /app

FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM base AS test
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY --chown=app:app . .
RUN chown app:app /app
USER app
CMD ["sh", "scripts/check.sh"]

FROM base AS runtime
COPY --from=deps /opt/venv /opt/venv
COPY .streamlit ./.streamlit
COPY src ./src
RUN chown app:app /app
USER app
EXPOSE 8501
CMD ["streamlit", "run", "src/console/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
