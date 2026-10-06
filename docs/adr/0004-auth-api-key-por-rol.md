# 0004 · Autenticación por API key por rol

- **Estado:** Aceptado
- **Fecha:** 2026-10-05

## Contexto
Hay dos roles de negocio con permisos distintos (coordinador escribe, operador consulta) en una demo local. Se requiere seguridad demostrable sin desviar esfuerzo del objetivo algorítmico.

## Decisión
- Encabezado `X-API-Key`, con una clave por rol (`coordinator`, `operator`) y una clave `internal` para la comunicación entre servicios.
- Las claves se definen en `.env` (generado con `make env`) y se comparan en tiempo constante.
- Al arrancar se rechazan las claves débiles, las de ejemplo o las repetidas.
- La consola pide la clave al usuario y no la guarda en su configuración.

## Alternativas consideradas
- **JWT + usuarios con contraseña (bcrypt):** es más realista, pero requiere un servicio o módulo de identidad, la gestión de usuarios y la expiración. El costo es de varios días y queda fuera del alcance del brief.
- **OAuth2/OIDC (Keycloak):** desproporcionado para una demo local.
- **Sin autenticación:** no demuestra el control de acceso por rol.

## Consecuencias
- La identidad es el **rol**, no la persona: no hay auditoría individual.
- Migrar a JWT más adelante solo cambiaría `core/security.py`, que es un único punto de autorización.
