# F1-B · Persistencia en PostgreSQL

- **Rama:** `feature/F1B-persistencia` · **Estado:** ✅ Terminada (con evidencia)
- **Dueño:** _(nombre)_
- **Lea antes:** [F1 (general)](F1-red-cobertura.md), [02-modelo-de-grafo](../02-modelo-de-grafo.md), [06-seguridad](../06-seguridad.md), [07-testing](../07-testing-y-harness.md)

## Objetivo
Persistir la red en PostgreSQL con SQLAlchemy 2.0 y Alembic. Para eso hay que implementar el puerto `NetworkRepository` (`application/ports.py`) de modo que pase **sin cambios** la suite de contrato `tests/contract/repository_contract.py`, y activarlo en `infrastructure/factory.py`.

## Archivos que puede modificar o crear (y solo estos)
- `src/network_service/infrastructure/orm.py`: agregar las tablas.
- `src/network_service/infrastructure/database.py` (crear): creación del engine.
- `src/network_service/infrastructure/sql_repository.py` (crear): `SqlAlchemyNetworkRepository`.
- `src/network_service/infrastructure/factory.py`: devolver el repositorio SQL.
- `alembic/versions/0001_create_network_tables.py` (crear).
- `tests/integration/test_sql_repository.py` (crear).
- `tests/unit/api/test_dependencies.py`: **solo** reemplazar `test_base_factory_uses_memory_repository` por `test_factory_uses_sql_repository`.
- `docs/features/F1B-persistencia.md` (este archivo) y **su fila** en `docs/README.md`.

Todo lo anterior está bajo `services/network-service/`, salvo la documentación. No agregue dependencias: SQLAlchemy, psycopg y Alembic ya están en `pyproject.toml`/`uv.lock`. No toque `alembic/env.py` (ya usa `Base.metadata`), ni `docker-compose*.yml` ni el `Makefile`.

## Esquema exacto (migración `0001`)

`revision = "0001"`, `down_revision = None`. `downgrade()` borra las tablas en orden inverso: edges, technicians, nodes.

```sql
CREATE TABLE nodes (
  id    VARCHAR(32) PRIMARY KEY,
  type  VARCHAR(4)  NOT NULL CONSTRAINT ck_nodes_type CHECK (type IN ('BASE','ZONE')),
  name  VARCHAR(80) NOT NULL
);
CREATE TABLE technicians (
  id        VARCHAR(32) PRIMARY KEY,
  node_id   VARCHAR(32) NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  position  INTEGER     NOT NULL,          -- orden del técnico dentro de la base (0..n-1)
  name      VARCHAR(80) NOT NULL,
  available BOOLEAN     NOT NULL
);
CREATE TABLE edges (
  id            VARCHAR(32) PRIMARY KEY,
  source        VARCHAR(32) NOT NULL REFERENCES nodes(id) ON DELETE RESTRICT,
  target        VARCHAR(32) NOT NULL REFERENCES nodes(id) ON DELETE RESTRICT,
  weight        DOUBLE PRECISION NOT NULL,
  bidirectional BOOLEAN NOT NULL,
  CONSTRAINT ck_edges_weight_range CHECK (weight > 0 AND weight <= 1440),
  CONSTRAINT ck_edges_no_self_loop CHECK (source <> target),
  CONSTRAINT uq_edges_source_target UNIQUE (source, target)
);
```

- En `orm.py`, declare las tablas con SQLAlchemy 2.0 (`Mapped`/`mapped_column`, o `Table`) con **los mismos nombres de tablas, columnas y constraints**. Esos metadatos deben coincidir con la migración.
- La migración se escribe **a mano**, con `op.create_table`, de forma explícita y legible. No use `--autogenerate` sin revisarla.

## `database.py`
```python
def create_db_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)
```

## `SqlAlchemyNetworkRepository(engine: Engine)`
- Implementa **todos** los métodos de `NetworkReader` y `NetworkWriter` con las firmas exactas del puerto.
- Cada método abre su propia transacción con `with engine.begin() as conn:` o `Session(engine)` + `commit`. `save_network` usa **una sola** transacción:
  - con `replace=True`: borrar `edges`, luego `technicians`, luego `nodes`, e insertar todo;
  - con `replace=False`: insertar solamente.
- Convertir filas en entidades: `Node.technicians` es una tupla ordenada por `position`; `NodeType(row.type)`; `float(weight)`.
- Listados con `ORDER BY id`.
- **Errores:** una violación de unicidad (`IntegrityError` con `orig.sqlstate == "23505"`) se traduce a `DuplicateIdError("El identificador ya existe.")`, y la transacción se revierte. Cualquier otro `IntegrityError` se relanza tal cual (no debería ocurrir: F1-A valida antes).
- **Consultas parametrizadas**, siempre con la API de SQLAlchemy. Nunca concatene SQL.
- `delete_node` y `delete_edge` de un id inexistente no hacen nada.

## `factory.py`
```python
def build_repository(settings: Settings) -> NetworkRepository:
    return SqlAlchemyNetworkRepository(create_db_engine(settings.database_url.get_secret_value()))
```
Crear el engine no abre conexión, así que las pruebas unitarias siguen funcionando con la URL falsa de `tests/conftest.py`.

## Pruebas obligatorias
**`tests/integration/test_sql_repository.py`** (marcar con `pytestmark = pytest.mark.integration`; usar el fixture `database_url` de `tests/integration/conftest.py`):
- [ ] `class TestSqlAlchemyRepository(RepositoryContract)` con un fixture `repository` que:
  1. aplica `alembic upgrade head` una vez por sesión (vea cómo lo hace `tests/integration/test_migrations.py`);
  2. antes de cada prueba ejecuta `TRUNCATE edges, technicians, nodes`;
  3. devuelve `SqlAlchemyNetworkRepository(create_db_engine(database_url))`.

  **Las ~16 pruebas heredadas deben pasar sin modificar la suite.**
- [ ] Las restricciones de la base de datos existen. Insertando directamente con SQLAlchemy Core, cada uno de estos casos lanza `IntegrityError`:
  - peso `0`;
  - peso `-5`;
  - peso `1441`;
  - `source == target`;
  - par `(source, target)` repetido;
  - `type = 'OTRO'`.
- [ ] Borrar un nodo con conexiones directamente en SQL falla (FK `RESTRICT`), y borrar una base elimina sus técnicos (`CASCADE`).
- [ ] Los datos persisten entre instancias: crear una red con una instancia del repositorio, leerla con **otra** instancia y obtener la misma red.
- [ ] `tests/integration/test_migrations.py` (ya existe) sigue en verde: upgrade, downgrade y upgrade, con tus tablas.

**`tests/unit/api/test_dependencies.py`**: `test_factory_uses_sql_repository` comprueba que `get_repository()` es una instancia de `SqlAlchemyNetworkRepository`.

## Verificación manual
```bash
make reset && make up        # base limpia; network-service aplica la migración 0001 al arrancar
docker compose logs network-service | grep -i "running upgrade"   # → "Running upgrade  -> 0001"
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\d edges"'
```

## Definition of Done
- [x] `make test-network` y `make test` en verde. Las pruebas de integración **se ejecutan** (no aparecen como `SKIPPED`).
- [x] La migración `0001` aplica, revierte y vuelve a aplicar.
- [x] El estado está actualizado en este archivo y en `docs/README.md`.
- [ ] PR con la plantilla completa.

## Evidencia

`make test-network`: harness en verde, 87 passed (26 de integración ejecutadas, 0 SKIPPED:
16 heredadas del contrato + peso 0/-5/1441 + self-loop + par repetido + tipo OTRO +
FK RESTRICT + CASCADE + persistencia entre instancias + migraciones upgrade/downgrade/upgrade).
`make test`: `OK: harness en verde para: network routing console`
(network 87 + routing 27 + console 11 passed).

`docker compose logs network-service | grep -i "running upgrade"`:

```text
network-service-1  | INFO  [alembic.runtime.migration] Running upgrade  -> 0001, Crea las tablas de la red (F1-B). Esquema exacto: docs/features/F1B-persistencia.md.
```

`docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\d edges"'`:

```text
                          Table "public.edges"
    Column     |         Type          | Collation | Nullable | Default
---------------+-----------------------+-----------+----------+---------
 id            | character varying(32) |           | not null |
 source        | character varying(32) |           | not null |
 target        | character varying(32) |           | not null |
 weight        | double precision      |           | not null |
 bidirectional | boolean               |           | not null |
Indexes:
    "edges_pkey" PRIMARY KEY, btree (id)
    "uq_edges_source_target" UNIQUE CONSTRAINT, btree (source, target)
Check constraints:
    "ck_edges_no_self_loop" CHECK (source::text <> target::text)
    "ck_edges_weight_range" CHECK (weight > 0::double precision AND weight <= 1440::double precision)
Foreign-key constraints:
    "edges_source_fkey" FOREIGN KEY (source) REFERENCES nodes(id) ON DELETE RESTRICT
    "edges_target_fkey" FOREIGN KEY (target) REFERENCES nodes(id) ON DELETE RESTRICT
```

Nota de implementación: las lecturas usan `Session` (no `Connection`), porque solo
`Session` materializa entidades ORM; con `Connection`, `scalars(select(NodeRow))`
devuelve la primera columna en lugar de la entidad.
