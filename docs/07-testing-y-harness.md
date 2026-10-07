# 07 · Pruebas y harness

## Definition of Done

> **Una tarea está terminada solo si `make test` termina en verde.** Esto aplica a personas y a IAs ([AGENTS.md](../AGENTS.md) §3).

## Qué ejecuta el harness

Cada servicio tiene una imagen Docker `test` (multi-stage) que ejecuta `scripts/check.sh`:

| Paso | Herramienta | Falla si… |
|---|---|---|
| Lint | `ruff check` | hay errores de estilo, imports, bugs comunes (B) o reglas de seguridad (S) |
| Formato | `ruff format --check` | el código no está formateado |
| Tipos | `mypy --strict` (src y tests) | hay errores de tipos |
| Seguridad del código | `bandit -r src` | hay hallazgos |
| Dependencias | `pip-audit` sobre `uv.lock` | hay un CVE conocido |
| Pruebas | `pytest` + `pytest-cov` | falla una prueba o la cobertura queda **< 85 %** (con ramas) |

En network-service, `make test-network` levanta además un **PostgreSQL efímero** (`network-db` en `docker-compose.test.yml`) y define `TEST_DATABASE_URL`. Así **se ejecutan** las pruebas de `tests/integration/` (migraciones y repositorio SQL). Al terminar, el contenedor se elimina. Sin esa variable, por ejemplo en una corrida local con `uv run pytest`, esas pruebas se omiten (`SKIPPED`).

### ¿Cómo sé que el harness corrió de verdad?

Cada servicio imprime los pasos `==> ruff`, `==> mypy`, `==> bandit`, `==> pip-audit` y `==> pytest`, y luego `N passed` con la cobertura. **Si `make test` imprime solo `OK` sin esos pasos, el harness no se ejecutó.**

Esto ocurrió en la Fase 0: el `Makefile` usaba una regla de patrón `test-%` con targets `.PHONY`, y GNU make no aplica reglas de patrón a targets `.PHONY`. Por eso los targets `test-*` son explícitos. Se verificó también el caso negativo: una prueba rota hace terminar `make test` con `Error 1`.

## Comandos

```bash
make test            # los 3 servicios (equivale a lo que corre la CI)
make test-network    # solo network-service
make test-routing    # solo routing-service
make test-console    # solo console
make smoke-f1        # humo de F1 contra la demo levantada (make up); reemplaza la red por la demo
```

Equivalentes sin `make`, por ejemplo en Windows:

```bash
docker compose -f docker-compose.test.yml run --rm --build network-tests
docker compose -f docker-compose.test.yml run --rm --build routing-tests
docker compose -f docker-compose.test.yml run --rm --build console-tests
docker compose -f docker-compose.test.yml down -v
sh scripts/smoke_f1.sh   # en Git Bash o WSL; requiere curl
```

Para iterar más rápido en local sin Docker (opcional, requiere [uv](https://docs.astral.sh/uv/)):

```bash
cd services/routing-service && uv sync && uv run pytest
```

## Organización de pruebas

```
services/<servicio>/tests/
  conftest.py        variables de entorno de prueba y fixtures (client, headers por rol)
  unit/              dominio, casos de uso, API, seguridad y errores, sin red ni BD
  integration/       PostgreSQL real (network-service): migraciones y repositorio SQL
  contract/          (network-service) suite que toda implementación del repositorio debe pasar
```

En network-service hay dos pruebas que **vigilan la base congelada de F1**:
- `tests/contract/repository_contract.py`: comportamiento exigido a cualquier `NetworkRepository` (LSP);
- `tests/unit/test_frozen_interfaces.py`: firmas de reglas y casos de uso que usan los otros carriles.

Lineamientos:
- **Algoritmos:** grafos pequeños construidos a mano y resultados exactos, incluidas las trazas. Los casos mínimos están en [04](04-algoritmos-bfs.md) y [05](05-algoritmos-dijkstra.md).
- **Patrón AAA** (Arrange, Act, Assert) y un comportamiento por prueba. Los nombres describen el comportamiento: `test_unreachable_zone_returns_covered_false`.
- **Dobles de prueba vía puertos:**
  - en routing-service, un `NetworkGateway` en memoria (ver `tests/unit/test_contracts.py`);
  - en network-service, un repositorio en memoria;
  - en la consola, `httpx.MockTransport` o `monkeypatch` de los clientes.
- **Consola:** se usa `streamlit.testing.v1.AppTest`. La lógica vive en módulos importables (`main_page.py`, `components/`) y `app.py` solo delega.
- **Errores:** todo código de error del [contrato](03-api.md) que emita un servicio tiene al menos una prueba.

## Pruebas de aceptación (Fase 3)

Cubren los 4 escenarios del brief contra la demo levantada (`make up`): éxito, zona inexistente, red desconectada y peso inválido. Se ejecutan con `make test-acceptance` (se agrega en la Fase 3).

## CI

`.github/workflows/ci.yml` ejecuta `make test` en cada push y PR a `main`. Un PR no se fusiona si la CI está en rojo.
