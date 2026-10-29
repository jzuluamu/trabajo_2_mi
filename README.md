# ServicioCerca · Cobertura y atención de menor costo

## Objetivo del proyecto

Construir un **MVP funcional** que reemplace las llamadas y el conocimiento informal con que
**ServicioCerca** decide, ante una solicitud de mantenimiento:

1. **¿La zona solicitada está dentro de la cobertura de alguna base?** Se responde con alcance en un grafo, usando **BFS**.
2. **¿Qué base y qué técnico pueden llegar con menor costo estimado, y por qué ruta?** Se responde con el camino de menor costo, usando **Dijkstra**.

El sistema modela la red operativa (bases, zonas y trayectos con tiempo positivo) como un **grafo dirigido y ponderado**. Expone la red por API y la presenta en una consola visual donde el operador entiende el resultado sin interpretar estructuras internas.

Es un trabajo académico de *Matemáticas para Informática*. Además de funcionar, el MVP debe demostrar:
- buenas prácticas de desarrollo y principios **SOLID**;
- seguridad por diseño;
- pruebas automatizadas;
- trabajo colaborativo de **4 personas** sobre git.

> Criterio de éxito del cliente: en una demo, el operador registra la red, consulta una zona,
> recibe una alternativa entendible y ve respuestas consistentes cuando la atención no es posible.

## Usuarios

| Rol | Qué hace | Permiso |
|---|---|---|
| Coordinador de operaciones | Registra bases, técnicos, zonas y conexiones | Lectura y escritura |
| Operador de atención | Consulta la cobertura y la alternativa de atención | Solo lectura |

## Features

| # | Feature | Servicio | Estado |
|---|---|---|---|
| F1 | [Red de cobertura](docs/features/F1-red-cobertura.md) | `network-service` | ✅ Terminada (con evidencia) |
| F2 | [Consulta de cobertura (BFS)](docs/features/F2-consulta-cobertura.md) | `routing-service` | ✅ Terminada (con evidencia) |
| F3 | [Alternativa de menor costo (Dijkstra)](docs/features/F3-menor-costo.md) | `routing-service` | ⛔ Fuera del alcance actual |
| F4 | [Consola de operación](docs/features/F4-consola.md) | `web` · `console` (en retiro) | 🟡 Consola web (React) con paridad de F1 y F2 |

> **Alcance actual: F1 y F2.** F1 se construyó en paralelo por 3 personas o agentes (ver
> [docs/features/F1-red-cobertura.md](docs/features/F1-red-cobertura.md)); F2 le agrega la consulta
> de cobertura con BFS ([docs/features/F2-consulta-cobertura.md](docs/features/F2-consulta-cobertura.md)).
> F3 queda fuera del alcance actual.

El estado vigente de cada feature y de las fases está en **[docs/README.md](docs/README.md)**.

## Stack

- **Servicios:** Python 3.12 · FastAPI · Pydantic v2 · PostgreSQL 16 · SQLAlchemy 2 · pytest · ruff · mypy · bandit · pip-audit · uv.
- **Consola web:** Node 24 · React 19 · Vite · TypeScript · Tailwind CSS v4 · shadcn/ui · TanStack Query · Cytoscape.js · Hono (BFF) · Vitest · ESLint.
- **Infraestructura:** Docker Compose. La consola Streamlit sigue disponible mientras se retira.
Las razones de cada elección están en [docs/adr/](docs/adr/).

```
navegador ──cookie──▶ [web :8080  SPA + BFF] ──X-API-Key──▶ [network-service :8001] ──▶ [PostgreSQL]
                              └───────────X-API-Key──▶ [routing-service :8002] ──snapshot──▶ network-service
```

## Inicio rápido

Solo necesita **Docker** (Desktop o Engine con Compose v2) y `make`.

```bash
make env     # crea .env con API keys y contraseña aleatorias
make up      # construye y levanta la demo
make test    # harness completo: lint, tipos, seguridad y pruebas
```

Después abra:
- la consola web: <http://localhost:8080> (la consola Streamlit sigue en <http://localhost:8501> mientras se retira);
- Swagger de cada servicio: <http://localhost:8001/docs> y <http://localhost:8002/docs>.

Para iniciar sesión en la consola, copie `COORDINATOR_API_KEY` u `OPERATOR_API_KEY` desde su `.env`.

El paso a paso completo para probar está en la **[guía de prueba manual](docs/10-guia-prueba-manual.md)**. Ejecute `make help` para ver todos los comandos.

## Documentación

Toda la documentación está indexada en **[docs/README.md](docs/README.md)**. Antes de escribir código o documentación, léala (es una regla obligatoria para personas e IAs: ver [AGENTS.md](AGENTS.md)).

## Estructura

```
services/network-service   F1: red de cobertura (dueño de los datos)
services/routing-service   F2 y F3: cobertura (BFS) y menor costo (Dijkstra)
services/web               F4: consola web (React + BFF Hono)
services/console           F4: consola Streamlit (en retiro)
seed/                      datos sintéticos de demostración
docs/                      documentación (fuente de verdad)
```
