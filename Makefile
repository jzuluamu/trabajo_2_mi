# ServicioCerca — comandos del proyecto. Todo corre en Docker (sin Python local).
# En Windows sin `make`, use los comandos equivalentes de docs/07-testing-y-harness.md.

COMPOSE      := docker compose
TEST_COMPOSE := docker compose -f docker-compose.test.yml
SERVICES     := network routing console

.DEFAULT_GOAL := help
.PHONY: help env up down reset logs ps test $(addprefix test-,$(SERVICES)) lock

help: ## Lista los comandos disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

env: ## Crea .env con secretos aleatorios a partir de .env.example
	docker run --rm -u "$$(id -u):$$(id -g)" -v "$(CURDIR):/work" -w /work python:3.12.8-slim python scripts/generate_env.py

up: ## Construye y levanta la demo (db, network, routing, console)
	@test -f .env || (echo "Falta .env: ejecute 'make env' primero." && exit 1)
	$(COMPOSE) up -d --build --wait
	@echo "Consola:  http://localhost:$${CONSOLE_PORT:-8501}"
	@echo "Swagger:  http://localhost:$${NETWORK_PORT:-8001}/docs  |  http://localhost:$${ROUTING_PORT:-8002}/docs"

down: ## Detiene la demo (conserva los datos)
	$(COMPOSE) down

reset: ## Detiene la demo y BORRA los datos de la base
	$(COMPOSE) down -v

logs: ## Sigue los logs de todos los servicios
	$(COMPOSE) logs -f

ps: ## Estado de los contenedores
	$(COMPOSE) ps

test: $(addprefix test-,$(SERVICES)) ## Harness completo (Definition of Done)
	@echo "OK: harness en verde para: $(SERVICES)"

test-%: ## Harness de un servicio: make test-network | test-routing | test-console
	$(TEST_COMPOSE) run --rm --build $*-tests

lock: ## Regenera los uv.lock tras cambiar dependencias en un pyproject.toml
	@for s in network-service routing-service console; do \
		docker run --rm -v "$(CURDIR)/services/$$s:/app" -w /app ghcr.io/astral-sh/uv:0.11.16-python3.12-bookworm-slim uv lock; \
	done
