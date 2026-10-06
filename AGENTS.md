# AGENTS.md — Reglas obligatorias para agentes de IA (y personas)

Este archivo es **canónico** para cualquier asistente de IA (Claude, Copilot, Cursor, Codex, Gemini, etc.) que trabaje en este repositorio. `CLAUDE.md` lo importa. Las reglas no son opcionales.

## 1. Leer la documentación ANTES de escribir

Antes de escribir **cualquier** línea de código **o de documentación**:

1. Lea [`docs/README.md`](docs/README.md), que es el índice, el estado de las features y las fases.
2. Lea los documentos de lo que va a tocar:

| Si toca… | Lea primero |
|---|---|
| Cualquier endpoint o payload | [`docs/03-api.md`](docs/03-api.md) (contrato congelado) |
| Nodos, aristas, dirección, pesos | [`docs/02-modelo-de-grafo.md`](docs/02-modelo-de-grafo.md) |
| BFS / cobertura | [`docs/04-algoritmos-bfs.md`](docs/04-algoritmos-bfs.md) + [`F2`](docs/features/F2-consulta-cobertura.md) |
| Dijkstra / menor costo | [`docs/05-algoritmos-dijkstra.md`](docs/05-algoritmos-dijkstra.md) + [`F3`](docs/features/F3-menor-costo.md) |
| Auth, secretos, Docker | [`docs/06-seguridad.md`](docs/06-seguridad.md) |
| Pruebas, harness | [`docs/07-testing-y-harness.md`](docs/07-testing-y-harness.md) |
| Ramas, PRs, commits | [`docs/08-colaboracion-git.md`](docs/08-colaboracion-git.md) |
| Arquitectura o decisiones | [`docs/01-arquitectura.md`](docs/01-arquitectura.md) + [`docs/adr/`](docs/adr/) |

Si la documentación contradice el código, **no adivine**. Señálelo y corrija primero la fuente equivocada.

## 2. Si hay cambios, se actualiza la documentación (mismo commit/PR)

Todo cambio de comportamiento, API, modelo, configuración o decisión debe actualizar la documentación en el **mismo PR**:

- Si cambia un endpoint o un payload, actualice `docs/03-api.md`. Ese PR lleva la etiqueta `contract-change` y lo revisan los dueños afectados.
- Si cambia el estado de una feature, actualice la tabla de `docs/README.md` y la de `README.md`, y el archivo `docs/features/F*.md`.
- Si agrega o cambia una variable de entorno, actualice `.env.example` y `docs/10-guia-prueba-manual.md`.
- Si toma una decisión de arquitectura nueva, agregue un ADR en `docs/adr/`.
- Si cambia el modelo o un algoritmo, actualice `docs/02`, `docs/04` o `docs/05`, incluidas las trazas de ejemplo.

Un PR con cambios de comportamiento y sin cambios en `docs/` está **incompleto**.

## 3. Definition of Done: el harness en verde

Una tarea **solo** está terminada si `make test` pasa. El harness ejecuta ruff, el formato, mypy strict, bandit, pip-audit y pytest con cobertura ≥ 85 %.

- Toda funcionalidad nueva trae pruebas unitarias, y las ramas de error también se prueban.
- No se desactivan reglas, pruebas ni umbrales para "hacer pasar" el harness. Si una excepción es legítima, se justifica en el PR.
- Si no puede ejecutar `make test`, dígalo explícitamente; nunca declare "listo" sin evidencia.

## 4. Arquitectura y código

- Las capas por servicio son `domain/` → `application/` → `infrastructure/` → `api/`. **`domain/` no hace I/O** (ni HTTP, ni BD, ni archivos).
- SOLID:
  - un caso de uso por clase;
  - los algoritmos implementan los `Protocol` de `routing_service/domain/strategies.py`;
  - las dependencias se inyectan (`Depends`) y no se instancian dentro de la lógica.
- Los microservicios **no comparten código** entre sí. Se comunican solo por HTTP y según el contrato.
- Los errores siguen el formato `{code, message, details}` con los códigos de `docs/03-api.md`.
- Los mensajes al usuario van en español y deben ser legibles. Los identificadores del código van en inglés.
- BFS y Dijkstra los **implementa el equipo**. No se usan networkx, scipy ni similares para resolverlos.

## 5. Seguridad

- Nunca commitear `.env`, claves ni tokens. Solo `.env.example`, con valores `CHANGE_ME_*`.
- Todo endpoint, salvo `/health`, exige `X-API-Key` con el rol correspondiente.
- Validar toda entrada con Pydantic. No reflejar la entrada del cliente en los errores. No exponer stack traces.

## 6. Git

- Ramas: `feature/F<n>-<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`. Nunca trabajar directo en `main`.
- Usar **Conventional Commits** (`feat(routing): ...`, `fix(network): ...`, `docs: ...`, `test: ...`).
- PR pequeños, con la plantilla completa, la CI en verde y 1 revisión.
