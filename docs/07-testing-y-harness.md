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

## Comandos

```bash
make test            # los 3 servicios (equivale a lo que corre la CI)
make test-network    # solo network-service
make test-routing    # solo routing-service
make test-console    # solo console
```

Equivalentes sin `make`, por ejemplo en Windows:

```bash
docker compose -f docker-compose.test.yml run --rm --build network-tests
docker compose -f docker-compose.test.yml run --rm --build routing-tests
docker compose -f docker-compose.test.yml run --rm --build console-tests
```

Para iterar más rápido en local sin Docker (opcional, requiere [uv](https://docs.astral.sh/uv/)):

```bash
cd services/routing-service && uv sync && uv run pytest
```

## Organización de pruebas

```
services/<servicio>/tests/
  conftest.py        variables de entorno de prueba y fixtures (client, headers por rol)
  unit/              dominio, casos de uso, seguridad y errores, sin red ni BD
  integration/       API + PostgreSQL (network-service, desde Fase 1) / cliente HTTP falso
```

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
