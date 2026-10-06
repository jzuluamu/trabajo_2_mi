# 06 · Seguridad

Modelo de amenaza del MVP: demo **local**, datos sintéticos y usuarios de confianza que no deben exceder su rol. El objetivo es demostrar prácticas correctas y proporcionadas, no blindaje de producción.

## Autenticación y autorización (RBAC por API key)

Ver [ADR 0004](adr/0004-auth-api-key-por-rol.md).

| Variable `.env` | Rol | Puede |
|---|---|---|
| `COORDINATOR_API_KEY` | `coordinator` | Leer y escribir la red, y consultar |
| `OPERATOR_API_KEY` | `operator` | Leer la red y consultar cobertura y rutas |
| `INTERNAL_API_KEY` | `internal` | Solo `GET /api/v1/network` (lo usa routing-service). La consola la rechaza |

- Se envían en el encabezado `X-API-Key`. Solo `/health` es público.
- La comparación se hace en **tiempo constante** (`secrets.compare_digest`) contra todas las claves, sin cortar en la primera coincidencia.
- Al arrancar, el servicio **falla** si alguna clave:
  - conserva el valor de ejemplo `CHANGE_ME_*`;
  - tiene menos de 16 caracteres;
  - coincide con la de otro rol.
- La autorización es una dependencia FastAPI `require_roles(...)` (`core/security.py`), declarada en cada endpoint.
- La consola **no guarda claves en su configuración**. Cada usuario ingresa la suya, y la consola obtiene su rol con `/auth/whoami`. La clave vive solo en la sesión del servidor Streamlit.

## Validación de entradas

- Pydantic v2 en todos los cuerpos y parámetros:
  - regex para los identificadores;
  - longitudes máximas;
  - `0 < weight ≤ 1440`.
- Restricciones en la base de datos como segunda barrera: `UNIQUE`, `CHECK (weight > 0)`, FK y `source <> target`.
- Las consultas usan el ORM o parámetros enlazados; nunca SQL concatenado.

## Manejo de errores

- El formato es único: `{code, message, details}`.
- Los errores de validación **no reflejan** el valor recibido, para no devolver datos del cliente.
- Las excepciones no controladas responden `500 INTERNAL_ERROR` genérico. El detalle va al log del servidor, nunca al cliente.
- Uvicorn corre con `--no-server-header`.

## Secretos

- `.env` está en `.gitignore`. Solo se versiona `.env.example`, con marcadores `CHANGE_ME_*`.
- `make env` genera `.env` con `secrets.token_urlsafe(32)`.
- Los secretos se tipan como `SecretStr`, por lo que no aparecen en `repr` ni en los logs.

## Contenedores e infraestructura

- Imágenes base con versión fijada (`python:3.12.8-slim`, `postgres:16.6-alpine`) y dependencias bloqueadas (`uv.lock`).
- Usuario **no root** (`app`).
- `cap_drop: ALL`, `no-new-privileges` y sistema de archivos `read_only` en las APIs, con `/tmp` en tmpfs.
- Los puertos se publican **solo en 127.0.0.1**. PostgreSQL no se publica y vive en la red `backend`, aislada de routing-service y de la consola.
- Healthchecks en todos los servicios.
- Streamlit corre con protección XSRF activa y sin telemetría.

## Verificación automática (harness)

- `bandit`: análisis estático de seguridad del código.
- `pip-audit`: CVEs conocidos en las dependencias bloqueadas.
- Pruebas de seguridad:
  - 401 sin clave o con clave inválida, y 403 por rol;
  - claves débiles o de ejemplo rechazadas;
  - errores 500 sin filtrar información interna.

## Límites conocidos (aceptados para el MVP)

- No hay TLS, porque todo es tráfico local. En producción iría detrás de un proxy con HTTPS.
- No hay rotación de claves, cuotas ni rate limiting.
- No hay auditoría por usuario individual: la identidad es el rol, no la persona.
