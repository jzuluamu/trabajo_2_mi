# 08 · Colaboración en git (4 personas)

## Reparto por feature y por carpeta (minimiza conflictos)

| Persona | Feature | Carpetas propias | Depende de |
|---|---|---|---|
| Persona 1 | F1 Red de cobertura | `services/network-service/**` | Contrato `03-api.md` |
| Persona 2 | F2 Cobertura (BFS) | `services/routing-service/src/routing_service/domain/coverage/`, endpoint `/coverage` | `Graph` (Fase 0) |
| Persona 3 | F3 Menor costo (Dijkstra) | `services/routing-service/src/routing_service/domain/cheapest_path/`, endpoints `/routes`, `/attention` | `Graph` (Fase 0) |
| Persona 4 | F4 Consola | `services/console/**` | Contrato (usa mocks hasta la Fase 2) |

Asigne los nombres reales en `docs/README.md` y los usuarios de GitHub en `.github/CODEOWNERS`.

**Archivos compartidos.** Su cambio requiere la revisión de los dueños afectados:
- `docs/03-api.md` (contrato);
- `routing_service/domain/graph.py`, `results.py` y `strategies.py` (dominio compartido entre F2 y F3);
- `routing_service/api/` y `main.py` (P2 y P3 registran routers distintos: un archivo por router);
- `docker-compose*.yml`, `Makefile`, `.env.example`, `AGENTS.md` y `CLAUDE.md`.

## Ramas

- `main` está protegida: solo recibe merges por PR, con la CI en verde y 1 aprobación.
- Ramas de trabajo, cortas y de pocos días:
  - `feature/F<n>-<slug>`, p. ej. `feature/F2-bfs-coverage`;
  - `fix/<slug>`, `docs/<slug>` y `chore/<slug>`.
- Antes de abrir el PR, actualice su rama: `git fetch && git rebase origin/main`.

## Commits — Conventional Commits

```
feat(routing): implementar BFS con traza por niveles
fix(network): rechazar conexión duplicada inversa bidireccional
docs(api): documentar código INVALID_ORIGIN
test(console): cubrir error de servicio no disponible
chore: actualizar uv.lock
```

El *scope* es el servicio (`network`, `routing` o `console`) o el área (`api`, `docs`, `ci`).

## Pull requests

- Use la plantilla [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md), que incluye la checklist de documentación y del harness.
- PR pequeños, idealmente de menos de 400 líneas, que hagan una sola cosa.
- Si cambia el contrato, use la etiqueta `contract-change`, actualice `docs/03-api.md` en el mismo PR y pida revisión a quienes lo consumen.
- Revisión: quien revisa ejecuta la guía de prueba de la feature y verifica que la documentación se actualizó.

## Flujo típico

```bash
git switch main && git pull
git switch -c feature/F2-bfs-coverage
# … leer docs/README.md, docs/04, docs/features/F2 … programar + pruebas + docs …
make test-routing          # iterar
make test                  # antes del PR
git add -p && git commit -m "feat(routing): implementar BFS con traza"
git push -u origin feature/F2-bfs-coverage   # abrir PR en GitHub
```
