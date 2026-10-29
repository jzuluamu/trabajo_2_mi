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
- La consola **no guarda claves en su configuración**. Cada usuario ingresa la suya, y la consola obtiene su rol con `/auth/whoami`. La clave vive solo en la sesión del servidor: en el BFF de la consola web ([ADR 0007](adr/0007-consola-web-react-bff.md)) o en la sesión de Streamlit. **Nunca llega al almacenamiento del navegador.**

## Validación de entradas

- Pydantic v2 en todos los cuerpos y parámetros:
  - regex para los identificadores;
  - longitudes máximas;
  - `0 < weight ≤ 1440`.
- Restricciones en la base de datos como segunda barrera: `UNIQUE`, `CHECK (weight > 0)`, FK y `source <> target`.
- Las consultas usan el ORM o parámetros enlazados; nunca SQL concatenado.

## Manejo de errores

- El formato es único: `{code, message, details}`.
- Los errores de validación **no reflejan** el valor recibido, para no devolver datos del cliente. Lo mismo vale para ids de ruta mal formados (`/nodes/<script>`): el `NODE_NOT_FOUND` / `EDGE_NOT_FOUND` responde con mensaje genérico y `details` vacío.
- Las excepciones no controladas responden `500 INTERNAL_ERROR` genérico. El detalle va al log del servidor, nunca al cliente.
- Uvicorn corre con `--no-server-header`.

## Consola web: BFF y sesión

Ver [ADR 0007](adr/0007-consola-web-react-bff.md) y [F4](features/F4-consola.md#endpoints-del-bff-internos-de-la-consola-no-son-parte-del-contrato).

- **La clave no llega al navegador:**
  - `POST /bff/session` la valida con `/auth/whoami` y la guarda en memoria del BFF;
  - el navegador recibe una cookie `sc_session` (`HttpOnly`, `SameSite=Strict`, `Path=/`) con un id aleatorio de 256 bits;
  - cada inicio de sesión crea un id nuevo y descarta el anterior;
  - la sesión caduca tras 8 h sin uso, y el BFF guarda como máximo 1000 sesiones.
- **CSRF:** los métodos que modifican exigen `X-ServicioCerca: 1`, que un formulario de otro sitio no puede enviar. La cookie `SameSite=Strict` es la segunda barrera.
- **Proxy con lista blanca:**
  - solo las rutas del [contrato](03-api.md), por método;
  - los ids en la ruta deben cumplir `[A-Za-z0-9_-]{1,64}`, lo que impide el path traversal (`..%2F`);
  - el resto responde `404 NOT_FOUND` sin contactar el servicio;
  - si un servicio responde 401, el BFF cierra la sesión.
- **Cabeceras:**
  - CSP con `default-src 'self'`, `script-src 'self'` (sin scripts en línea ni `eval`), `connect-src 'self'`, `object-src 'none'` y `frame-ancestors 'none'`;
  - `style-src` admite `'unsafe-inline'` porque Radix, sonner y Cytoscape fijan estilos en línea;
  - `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` y `Cache-Control: no-store` en `/bff`.
- **Errores:** se usa el formato `{code, message, details}` y no se refleja la entrada. Un error inesperado responde `500 INTERNAL_ERROR` genérico, y el detalle va solo al log.
- **Cuerpos:** máximo 2 MB (`PAYLOAD_TOO_LARGE`); la importación de red es el caso más grande.
- **Datos de la API:** React escapa el texto. Cytoscape dibuja en un canvas y muestra las etiquetas como texto plano. No se usa `dangerouslySetInnerHTML`.
- **Contenedor:** `node:24.19.0-alpine3.24` fijado, usuario no root `app`, `read_only`, `cap_drop: ALL` y `no-new-privileges`. Solo se instalan las dependencias del BFF (`hono`, `@hono/node-server`), y el puerto se publica en `127.0.0.1`.
- **Límite conocido:** las sesiones viven en memoria, así que reiniciar el contenedor `web` cierra todas. Con varias réplicas haría falta un almacén compartido.

## Consola Streamlit (en retiro): grafo embebido

Ver [ADR 0006](adr/0006-grafo-pyvis-embebido-seguro.md):
- el mapa va en un iframe con **origen opaco** (URL `data:`);
- tiene CSP `default-src 'none'` y `script-src` solo con los hash de sus dos scripts;
- no carga recursos externos;
- los datos de la API se serializan con `tojson` y se muestran como texto plano;
- los nombres que entran en Markdown de Streamlit se escapan (`md_escape`).

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

- `bandit`: análisis estático de seguridad del código Python.
- `pip-audit` y `npm audit`: CVEs conocidos en las dependencias bloqueadas (`uv.lock` y `package-lock.json`).
- Pruebas de seguridad:
  - 401 sin clave o con clave inválida, y 403 por rol;
  - claves débiles o de ejemplo rechazadas;
  - errores 500 sin filtrar información interna;
  - en el BFF: la cookie no contiene la clave, CSRF, lista blanca y path traversal, caducidad de la sesión, CSP y límite de tamaño (`services/web/tests/server/`).

## Límites conocidos (aceptados para el MVP)

- No hay TLS, porque todo es tráfico local. En producción iría detrás de un proxy con HTTPS.
- No hay rotación de claves, cuotas ni rate limiting.
- No hay auditoría por usuario individual: la identidad es el rol, no la persona.
