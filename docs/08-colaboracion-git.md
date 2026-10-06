# 08 · Colaboración en git (4 personas)

## Reparto actual: F1 en 3 carriles (minimiza conflictos)

| Persona / agente | Carril | Rama | Archivos propios |
|---|---|---|---|
| Persona A | F1-A Dominio y casos de uso | `feature/F1A-dominio-casos-de-uso` | `domain/rules.py`, `application/use_cases.py` y sus pruebas |
| Persona B | F1-B Persistencia | `feature/F1B-persistencia` | `infrastructure/{orm,database,sql_repository,factory}.py`, `alembic/versions/` y pruebas de integración |
| Persona C | F1-C API REST | `feature/F1C-api-rest` | `api/{schemas,nodes,edges,network,dependencies}.py` y sus pruebas |
| Integrador | F1-D Integración | `feature/F1D-integracion` | Prueba punta a punta, consola y cierre de la documentación |

La tabla completa de propiedad de archivos, incluidos los **congelados**, está en [features/F1-red-cobertura.md](features/F1-red-cobertura.md#propiedad-de-archivos-services-network-service). **Regla de oro:** si su carril necesita modificar un archivo que no es suyo, **no lo haga**. Avise al grupo y se decide con un PR `contract-change`.

Asigne los nombres reales en `docs/README.md` y los usuarios de GitHub en `.github/CODEOWNERS`.

**Documentación compartida:** cada carril edita solo **su fila** de la tabla de estado de `docs/README.md` y su archivo `docs/features/F1X-*.md`. Es la única fuente probable de conflictos de merge, y se resuelve conservando las filas de todos.

## Ramas

- `main` está protegida: solo recibe merges por PR, con la CI en verde y 1 aprobación.
- Ramas de trabajo, cortas y de pocos días:
  - `feature/F<n>-<slug>`, p. ej. `feature/F1B-persistencia`;
  - `fix/<slug>`, `docs/<slug>` y `chore/<slug>`.
- Antes de abrir el PR, actualice su rama: `git fetch && git rebase origin/main`.

## Commits — Conventional Commits

```
feat(network): agregar migración 0001 con tablas de la red
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
git switch -c feature/F1A-dominio-casos-de-uso
# … leer docs/README.md, docs/features/F1-red-cobertura.md y F1A … programar + pruebas + docs …
make test-network          # iterar
make test                  # antes del PR
git add -p && git commit -m "feat(network): implementar reglas de validación del dominio"
git push -u origin feature/F1A-dominio-casos-de-uso   # abrir PR en GitHub
```
