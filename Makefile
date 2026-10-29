# ServicioCerca — comandos del proyecto. Todo corre en Docker (sin Python local).
# En Windows sin `make`, use los comandos equivalentes de docs/07-testing-y-harness.md.

COMPOSE      := docker compose
TEST_COMPOSE := docker compose -f docker-compose.test.yml
SERVICES     := network routing console web
NODE_IMAGE   := node:24.19.0-alpine3.24

.DEFAULT_GOAL := help
.PHONY: help env up down reset logs ps test test-network test-routing test-console test-web smoke-f1 smoke-f2 lock

help: ## Lista los comandos disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

env: ## Crea .env con secretos aleatorios a partir de .env.example
	docker run --rm -u "$$(id -u):$$(id -g)" -v "$(CURDIR):/work" -w /work python:3.12.8-slim python scripts/generate_env.py

up: ## Construye y levanta la demo (db, network, routing, console, web)
	@test -f .env || (echo "Falta .env: ejecute 'make env' primero." && exit 1)
	$(COMPOSE) up -d --build --wait
	@echo "Consola web: http://localhost:$${WEB_PORT:-8080}"
	@echo "Consola (Streamlit, en retiro): http://localhost:$${CONSOLE_PORT:-8501}"
	@echo "Swagger:  http://localhost:$${NETWORK_PORT:-8001}/docs  |  http://localhost:$${ROUTING_PORT:-8002}/docs"

down: ## Detiene la demo (conserva los datos)
	$(COMPOSE) down

reset: ## Detiene la demo y BORRA los datos de la base
	$(COMPOSE) down -v

logs: ## Sigue los logs de todos los servicios
	$(COMPOSE) logs -f

ps: ## Estado de los contenedores
	$(COMPOSE) ps

# Nota: los targets test-* son explícitos a propósito. GNU make NO aplica reglas de patrón
# (test-%) a targets .PHONY: con un patrón, `make test` imprimía OK sin ejecutar nada.
test: test-network test-routing test-console test-web ## Harness completo (Definition of Done)
	@echo "OK: harness en verde para: $(SERVICES)"

test-network: ## Harness de network-service
	$(TEST_COMPOSE) run --rm --build network-tests; status=$$?; $(TEST_COMPOSE) down -v --remove-orphans >/dev/null 2>&1; exit $$status

test-routing: ## Harness de routing-service
	$(TEST_COMPOSE) run --rm --build routing-tests; status=$$?; $(TEST_COMPOSE) down -v --remove-orphans >/dev/null 2>&1; exit $$status

test-console: ## Harness de console
	$(TEST_COMPOSE) run --rm --build console-tests; status=$$?; $(TEST_COMPOSE) down -v --remove-orphans >/dev/null 2>&1; exit $$status

test-web: ## Harness de la consola web (eslint, prettier, tsc, npm audit, vitest)
	$(TEST_COMPOSE) run --rm --build web-tests; status=$$?; $(TEST_COMPOSE) down -v --remove-orphans >/dev/null 2>&1; exit $$status

smoke-f1: ## Humo de F1 contra la demo levantada (reemplaza la red por la demo)
	@sh scripts/smoke_f1.sh

smoke-f2: ## Humo de F2 contra la demo levantada (reemplaza la red por la demo)
	@sh scripts/smoke_f2.sh

lock: ## Regenera los uv.lock (Python) y el package-lock.json (web) tras cambiar dependencias
	@for s in network-service routing-service console; do \
		docker run --rm -v "$(CURDIR)/services/$$s:/app" -w /app ghcr.io/astral-sh/uv:0.11.16-python3.12-bookworm-slim uv lock; \
	done
	docker run --rm -u "$$(id -u):$$(id -g)" -e HOME=/tmp -v "$(CURDIR)/services/web:/app" -w /app $(NODE_IMAGE) npm install --package-lock-only --ignore-scripts --no-audit --no-fund
