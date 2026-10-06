# F1 · Prompts para los agentes (Claude Code / Codex)

Cada integrante abre **su propia copia** del repositorio en `main` actualizado, con su agente de IA, y pega **su** prompt completo. Los prompts sirven igual para Claude Code (lee `CLAUDE.md`) y para Codex (lee `AGENTS.md`).

Antes de pegar el prompt, el humano debe haber hecho, una sola vez, los pasos de la guía [10 · Inicio rápido](../10-guia-prueba-manual.md#inicio-rápido-para-cada-integrante):
- `make env`;
- `make up`;
- `make test` en verde, con los pasos `==>` visibles.

---

## Prompt F1-A · Dominio y casos de uso

```text
Eres el agente del carril F1-A (Dominio y casos de uso) del proyecto ServicioCerca. Trabajas en
paralelo con otros dos agentes (F1-B persistencia, F1-C API) sobre una base congelada.

1. LECTURA OBLIGATORIA antes de escribir cualquier línea (código o docs), en este orden:
   AGENTS.md, docs/README.md, docs/features/F1-red-cobertura.md (en especial la tabla
   "Propiedad de archivos"), docs/features/F1A-dominio-casos-de-uso.md (TU especificación),
   docs/02-modelo-de-grafo.md, docs/03-api.md. Luego lee el código existente:
   services/network-service/src/network_service/domain/{models,errors,rules}.py,
   application/{ports,use_cases}.py, infrastructure/memory_repository.py y
   tests/unit/test_frozen_interfaces.py.

2. RAMA: git switch main && git pull && git switch -c feature/F1A-dominio-casos-de-uso

3. ALCANCE: implementa exactamente lo que dice docs/features/F1A-dominio-casos-de-uso.md:
   - cuerpos de domain/rules.py y application/use_cases.py (mensajes, details y ORDEN de errores
     tal cual la especificación);
   - pruebas en tests/unit/domain/ y tests/unit/application/ cubriendo TODA la checklist de la
     especificación (verifica code y details, no solo el tipo de excepción).
   Solo puedes modificar/crear los archivos listados en "Archivos que puede modificar" de tu
   especificación. NO cambies firmas, models.py, errors.py, ports.py, memory_repository.py,
   pruebas ajenas, pyproject.toml ni uv.lock. Sin dependencias nuevas. Si algo de la
   especificación es ambiguo o parece contradecir el código, DETENTE y pregúntame; no inventes.

4. VERIFICACIÓN (tu criterio de OK): `make test-network` mientras iteras y `make test` al final.
   Debe verse "==> ruff ... ==> pytest", "N passed" y cobertura ≥ 85 % (apunta a 100 % en
   rules.py y use_cases.py). tests/unit/test_frozen_interfaces.py debe seguir verde sin cambios.
   Nunca declares "listo" sin pegar la salida real.

5. DOCUMENTACIÓN: actualiza el estado y la sección "Evidencia" de
   docs/features/F1A-dominio-casos-de-uso.md y SOLO tu fila (F1-A) en docs/README.md.

6. GIT: commits pequeños con Conventional Commits, p. ej.
   "feat(network): implementar reglas de validación del dominio",
   "feat(network): implementar casos de uso de la red", "test(network): ...".
   Haz `git fetch origin && git rebase origin/main` antes de subir. Luego
   `git push -u origin feature/F1A-dominio-casos-de-uso` y dame el texto del PR usando
   .github/PULL_REQUEST_TEMPLATE.md (no hagas merge).

7. REPORTE FINAL: archivos cambiados, resumen de reglas implementadas, salida de `make test`
   (pasos y cobertura) y cualquier duda o desvío respecto a la especificación.
```

---

## Prompt F1-B · Persistencia PostgreSQL

```text
Eres el agente del carril F1-B (Persistencia PostgreSQL) del proyecto ServicioCerca. Trabajas en
paralelo con otros dos agentes (F1-A dominio, F1-C API) sobre una base congelada.

1. LECTURA OBLIGATORIA antes de escribir cualquier línea (código o docs), en este orden:
   AGENTS.md, docs/README.md, docs/features/F1-red-cobertura.md (en especial la tabla
   "Propiedad de archivos"), docs/features/F1B-persistencia.md (TU especificación),
   docs/02-modelo-de-grafo.md, docs/06-seguridad.md, docs/07-testing-y-harness.md. Luego lee:
   services/network-service/src/network_service/application/ports.py, domain/{models,errors}.py,
   infrastructure/{memory_repository,factory,orm}.py, alembic/env.py, alembic.ini,
   tests/contract/repository_contract.py, tests/integration/{conftest,test_migrations}.py,
   tests/unit/api/test_dependencies.py y docker-compose.test.yml.

2. RAMA: git switch main && git pull && git switch -c feature/F1B-persistencia

3. ALCANCE: implementa exactamente lo que dice docs/features/F1B-persistencia.md:
   - tablas en infrastructure/orm.py y migración escrita a mano
     alembic/versions/0001_create_network_tables.py (revision "0001"), con el esquema EXACTO
     (nombres de tablas, columnas y constraints) de la especificación;
   - infrastructure/database.py y infrastructure/sql_repository.py (SqlAlchemyNetworkRepository)
     cumpliendo el puerto y la suite de contrato SIN modificarla;
   - infrastructure/factory.py devolviendo el repositorio SQL;
   - tests/integration/test_sql_repository.py (hereda RepositoryContract + pruebas de constraints,
     FK y persistencia) y el ajuste de UNA prueba en tests/unit/api/test_dependencies.py.
   Solo puedes modificar/crear los archivos listados en tu especificación. NO toques
   alembic/env.py, la suite de contrato, docker-compose*.yml, Makefile, pyproject.toml ni
   uv.lock. Sin dependencias nuevas. Consultas siempre parametrizadas (API de SQLAlchemy).
   Si algo es ambiguo o contradice el código, DETENTE y pregúntame; no inventes.

4. VERIFICACIÓN (tu criterio de OK): `make test-network` y `make test` al final. Las pruebas de
   tests/integration/ deben EJECUTARSE (no SKIPPED) y pasar. Además verifica en la demo:
   `make reset && make up` y `docker compose logs network-service | grep -i "running upgrade"`
   debe mostrar "-> 0001". Nunca declares "listo" sin pegar la salida real.

5. DOCUMENTACIÓN: actualiza estado y "Evidencia" de docs/features/F1B-persistencia.md (incluye
   la salida de `\d edges`) y SOLO tu fila (F1-B) en docs/README.md.

6. GIT: commits pequeños con Conventional Commits, p. ej.
   "feat(network): agregar tablas y migración 0001 de la red",
   "feat(network): implementar repositorio SQLAlchemy", "test(network): ...".
   `git fetch origin && git rebase origin/main` antes de subir; luego
   `git push -u origin feature/F1B-persistencia` y dame el texto del PR con
   .github/PULL_REQUEST_TEMPLATE.md (no hagas merge).

7. REPORTE FINAL: archivos cambiados, esquema creado, salida de `make test` (con las pruebas de
   integración ejecutadas), evidencia de la migración y cualquier duda o desvío.
```

---

## Prompt F1-C · API REST

```text
Eres el agente del carril F1-C (API REST) del proyecto ServicioCerca. Trabajas en paralelo con
otros dos agentes (F1-A dominio, F1-B persistencia) sobre una base congelada.

1. LECTURA OBLIGATORIA antes de escribir cualquier línea (código o docs), en este orden:
   AGENTS.md, docs/README.md, docs/features/F1-red-cobertura.md (en especial la tabla
   "Propiedad de archivos"), docs/features/F1C-api-rest.md (TU especificación),
   docs/03-api.md (CONTRATO), docs/06-seguridad.md. Luego lee:
   services/network-service/src/network_service/main.py, api/{dependencies,error_mapping,
   nodes,edges,network,auth}.py, core/{security,errors}.py, domain/{models,errors}.py,
   application/{ports,use_cases}.py, tests/conftest.py y tests/unit/test_security.py (patrones).

2. RAMA: git switch main && git pull && git switch -c feature/F1C-api-rest

3. ALCANCE: implementa exactamente lo que dice docs/features/F1C-api-rest.md:
   - api/schemas.py (solo tipos y forma; las reglas de negocio las valida el dominio);
   - los 9 endpoints en api/nodes.py, api/edges.py y api/network.py (routers ya registrados en
     main.py), con roles, status codes y response_model del contrato;
   - proveedores provide_* en api/dependencies.py (sin tocar get_repository);
   - pruebas en tests/unit/api/test_{nodes,edges,network}_api.py usando dependency_overrides
     con FAKES de los casos de uso (los casos de uso reales los implementa F1-A en paralelo; tus
     pruebas NO deben depender de ellos), cubriendo TODA la checklist de la especificación.
   Solo puedes modificar/crear los archivos listados en tu especificación. NO toques main.py,
   error_mapping.py, core/, domain/, application/, pruebas ajenas, pyproject.toml ni uv.lock. No
   captures DomainError en los routers. Si algo es ambiguo o contradice el contrato, DETENTE y
   pregúntame; no inventes ni cambies el contrato.

4. VERIFICACIÓN (tu criterio de OK): `make test-network` y `make test` al final, con los pasos
   "==> ruff ... ==> pytest", "N passed" y cobertura ≥ 85 %. Revisa además Swagger en
   http://localhost:8001/docs tras `make up` (las 9 rutas visibles). Nunca declares "listo" sin
   pegar la salida real.

5. DOCUMENTACIÓN: marca ✅ los endpoints implementados en docs/03-api.md, actualiza estado y
   "Evidencia" de docs/features/F1C-api-rest.md y SOLO tu fila (F1-C) en docs/README.md.

6. GIT: commits pequeños con Conventional Commits, p. ej.
   "feat(network): agregar esquemas Pydantic de la red",
   "feat(network): exponer endpoints de nodos, conexiones y red", "test(network): ...".
   `git fetch origin && git rebase origin/main` antes de subir; luego
   `git push -u origin feature/F1C-api-rest` y dame el texto del PR con
   .github/PULL_REQUEST_TEMPLATE.md (no hagas merge).

7. REPORTE FINAL: archivos cambiados, tabla de endpoints implementados, salida de `make test` y
   cualquier duda o desvío respecto al contrato.
```

---

## Prompt F1-D · Integración (integrador, cuando A, B y C estén en `main`)

```text
Eres el agente integrador de Feature 1 (carril F1-D) del proyecto ServicioCerca. F1-A, F1-B y
F1-C ya están fusionados en main.

1. LECTURA OBLIGATORIA antes de escribir: AGENTS.md, docs/README.md,
   docs/features/F1-red-cobertura.md, F1A/F1B/F1C (para conocer lo construido),
   docs/features/F1D-integracion.md (TU especificación), docs/03-api.md, docs/adr/0005 y
   docs/10-guia-prueba-manual.md. Revisa el código actual de services/network-service y
   services/console.

2. RAMA: git switch main && git pull && git switch -c feature/F1D-integracion

3. ALCANCE: exactamente docs/features/F1D-integracion.md: prueba punta a punta de la API,
   scripts/smoke_f1.sh + `make smoke-f1` (incluida persistencia tras reiniciar), interfaz mínima
   en la consola (ver red; coordinador: crear/borrar nodos y conexiones, cargar red demo) con
   pruebas, y cierre de documentación con evidencia. Antes de empezar ejecuta
   `make reset && make up && make test` y reporta cualquier falla de integración entre carriles
   ANTES de corregirla.

4. VERIFICACIÓN: `make reset && make up && make test && make smoke-f1` en verde y recorrido de la
   guía 10 (sección F1). Pega la salida real.

5. GIT: Conventional Commits, rebase sobre origin/main, push de la rama y texto del PR con la
   plantilla (no hagas merge).
```
