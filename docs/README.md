# Documentación de ServicioCerca — Índice

> **Regla obligatoria** ([AGENTS.md](../AGENTS.md)): lea este índice y los documentos relacionados
> antes de escribir código o documentación, y actualícelos en el mismo PR si cambia algo.

## Estado de features

| # | Feature | Servicio | Dueño | Estado | Especificación |
|---|---|---|---|---|---|
| F1 | Red de cobertura | `network-service` | Persona 1 | ⏳ Pendiente (Fase 1) | [F1](features/F1-red-cobertura.md) |
| F2 | Consulta de cobertura (BFS) | `routing-service` | Persona 2 | ⏳ Pendiente (Fase 1) | [F2](features/F2-consulta-cobertura.md) |
| F3 | Alternativa de menor costo (Dijkstra) | `routing-service` | Persona 3 | ⏳ Pendiente (Fase 1) | [F3](features/F3-menor-costo.md) |
| F4 | Consola de operación | `console` | Persona 4 | 🟡 Base lista (login + estado) | [F4](features/F4-consola.md) |

Leyenda: ⏳ pendiente · 🟡 en progreso · ✅ terminada (con evidencia) · ⛔ bloqueada

## Estado de fases

| Fase | Contenido | Estado |
|---|---|---|
| 0 — Fundaciones | Docker, harness, seguridad base, contratos, documentación | ✅ Terminada |
| 1 — Features en paralelo | F1, F2, F3 y F4 contra un mock | ⏳ Siguiente |
| 2 — Integración | Servicios reales extremo a extremo y visualización | ⏳ |
| 3 — Aceptación y evidencia | 4 escenarios del brief y evidencias | ⏳ |
| 4 — Cambio docente | Requisito por definir | ⏳ |

Detalle en [09-fases-y-roadmap.md](09-fases-y-roadmap.md).

## Documentos

| Documento | Para qué sirve |
|---|---|
| [Brief del cliente](../06-brief-serviciocerca.md) | Enunciado original del trabajo (fuente de los requisitos) |
| [00-vision-y-alcance.md](00-vision-y-alcance.md) | Problema, usuarios, alcance y fuera de alcance |
| [01-arquitectura.md](01-arquitectura.md) | Microservicios, capas, flujos y SOLID |
| [02-modelo-de-grafo.md](02-modelo-de-grafo.md) | Qué es cada nodo y arista, la dirección, los pesos y las justificaciones |
| [03-api.md](03-api.md) | **Contrato** de endpoints, errores y ejemplos |
| [04-algoritmos-bfs.md](04-algoritmos-bfs.md) | Cobertura: definición, BFS, justificación y traza |
| [05-algoritmos-dijkstra.md](05-algoritmos-dijkstra.md) | Menor costo: Dijkstra, pesos, contraejemplo y traza |
| [06-seguridad.md](06-seguridad.md) | Roles, API keys, secretos y endurecimiento |
| [07-testing-y-harness.md](07-testing-y-harness.md) | Harness, Definition of Done y cómo probar |
| [08-colaboracion-git.md](08-colaboracion-git.md) | Ramas, PRs, commits y reparto entre 4 personas |
| [09-fases-y-roadmap.md](09-fases-y-roadmap.md) | Plan por fases y checkpoints humanos |
| [10-guia-prueba-manual.md](10-guia-prueba-manual.md) | Paso a paso para probar la demo y el `.env` |
| [adr/](adr/) | Registro de decisiones de arquitectura |
| [features/](features/) | Especificación, criterios de aceptación y evidencia por feature |

## Decisiones (ADR)

| ADR | Decisión |
|---|---|
| [0001](adr/0001-stack-python-fastapi-postgres.md) | Python + FastAPI + PostgreSQL |
| [0002](adr/0002-microservicios-por-contexto.md) | Microservicios por contexto de negocio, no por algoritmo |
| [0003](adr/0003-modelo-de-grafo.md) | Técnicos como atributo de la base y grafo dirigido con aristas bidireccionales |
| [0004](adr/0004-auth-api-key-por-rol.md) | Autenticación por API key por rol |
| [0005](adr/0005-consola-streamlit.md) | Consola en Streamlit |
