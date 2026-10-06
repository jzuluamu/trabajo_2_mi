# 10 · Guía de prueba manual

Paso a paso para que una **persona** compruebe cada fase. Requisitos: Docker Desktop (o Engine con Compose v2) en ejecución y `make`. En Windows sin `make`, use los comandos `docker compose` equivalentes de [07](07-testing-y-harness.md).

## Inicio rápido para cada integrante

1. Instale Git y Docker Desktop, y ábralo: debe estar corriendo.
2. Clone el repositorio y entre a la carpeta:

   ```bash
   git clone https://github.com/jzuluamu/trabajo_2_mi.git && cd trabajo_2_mi
   ```

3. Cree su `.env` (solo la primera vez):

   ```bash
   make env
   ```

4. Levante los contenedores. Termina cuando todos están *healthy*:

   ```bash
   make up
   ```

5. Compruebe que `db`, `network-service`, `routing-service` y `console` estén `Up (healthy)`, y que ninguno quede en `Restarting`:

   ```bash
   docker compose ps
   ```

6. Ejecute el harness:

   ```bash
   make test
   ```

   Debe ver, **por cada servicio**, los pasos `==> ruff … ==> pytest` y `N passed`. Al final debe aparecer `OK: harness en verde para: network routing console`. Si solo aparece `OK`, sin esos pasos, su copia está desactualizada: haga `git pull`.

## Configurar `.env` (una sola vez)

```bash
make env
```

Crea `.env` a partir de `.env.example` y reemplaza cada `CHANGE_ME_*` por un secreto aleatorio. **No necesita editar nada más.** Si `.env` ya existe, no lo sobrescribe.

| Variable | ¿Debe cambiarla? | Notas |
|---|---|---|
| `POSTGRES_PASSWORD` | La genera `make env` | Si la cambia después de crear la base, ejecute `make reset` (borra los datos) |
| `POSTGRES_USER`, `POSTGRES_DB` | No | Igual que la anterior: cambiarlas requiere `make reset` |
| `COORDINATOR_API_KEY` | La genera `make env` | Úsela para iniciar sesión como **coordinador** |
| `OPERATOR_API_KEY` | La genera `make env` | Úsela para iniciar sesión como **operador** |
| `INTERNAL_API_KEY` | La genera `make env` | Solo entre servicios; la consola la rechaza |
| `NETWORK_PORT`, `ROUTING_PORT`, `CONSOLE_PORT` | Solo si el puerto está ocupado | Por defecto 8001, 8002 y 8501 |
| `LOG_LEVEL` | Opcional | `DEBUG` para más detalle |

Si edita las claves a mano, deben tener al menos 16 caracteres, ser distintas entre sí y no empezar por `CHANGE_ME`. Si no cumplen, el servicio no arranca. Revise el motivo con `make logs`.

Para ver sus claves:

```bash
grep API_KEY .env
```

## Fase 0

1. **Levantar:**

   ```bash
   make up
   ```

   Esperado: termina sin errores e imprime las URLs.

2. **Estado:**

   ```bash
   make ps
   ```

   Esperado: `db`, `network-service`, `routing-service` y `console` en estado `healthy`.

3. **Salud de las APIs:**

   ```bash
   curl http://localhost:8001/health
   ```

   ```bash
   curl http://localhost:8002/health
   ```

   Esperado: `{"status":"ok",...}` en cada una.

4. **Seguridad:**

   ```bash
   curl -i http://localhost:8001/api/v1/auth/whoami
   ```

   Esperado: `401` con `UNAUTHENTICATED`.

   Luego, reemplazando `<OPERATOR_API_KEY>` por su clave:

   ```bash
   curl -H "X-API-Key: <OPERATOR_API_KEY>" http://localhost:8001/api/v1/auth/whoami
   ```

   Esperado: `{"role":"operator"}`.

5. **Swagger:** abra <http://localhost:8001/docs> y <http://localhost:8002/docs>.

6. **Consola:** abra <http://localhost:8501>.
   1. Verá "network-service: operativo" y "routing-service: operativo".
   2. Pegue una clave incorrecta en la barra lateral: verá el mensaje "API key inválida.".
   3. Pegue `OPERATOR_API_KEY`: verá "Rol: Operador de atención".
   4. Pulse "Cerrar sesión" y repita con `COORDINATOR_API_KEY`.
   5. Pegue `INTERNAL_API_KEY`: verá que la rechaza como usuario de la consola.

7. **Respuesta ante una caída:**

   ```bash
   docker compose stop routing-service
   ```

   Recargue la consola: verá "routing-service: no disponible" sin que la aplicación se rompa. Después vuelva a levantarlo:

   ```bash
   docker compose start routing-service
   ```

8. **Harness:**

   ```bash
   make test
   ```

   Esperado: `OK: harness en verde para: network routing console`.

9. **Apagar:**

   ```bash
   make down
   ```

   O `make reset` para borrar también los datos.

## F1 · Red de cobertura

F1-D completa esta sección al integrar. Mientras los carriles están en construcción, cada uno verifica lo suyo:
- **F1-A:** `make test-network`.
- **F1-B:** `make reset && make up` y, en `docker compose logs network-service`, la línea `Running upgrade -> 0001`.
- **F1-C:** Swagger en <http://localhost:8001/docs>.

Con el repositorio en memoria (antes de que se fusione F1-B), los datos se pierden al reiniciar.

## Fases posteriores (fuera del alcance actual)

Se completan al cerrar cada fase (ver [09](09-fases-y-roadmap.md)). Recorrido previsto para la demo final:
- cargar la red demo;
- consultar la cobertura de `B_NORTE`;
- consultar la ruta `B_NORTE → Z_CENTRO` (15 min, contra 30 por el camino de menos tramos);
- consultar la mejor atención para `Z_COLINA` (B_SUR) y para `Z_FUENTE` (no atendible);
- probar una zona inexistente;
- intentar registrar una conexión con peso `-5`, que debe rechazarse con `INVALID_WEIGHT`.

## Problemas comunes

| Síntoma | Causa probable / solución |
|---|---|
| `Falta .env` | Ejecute `make env` |
| Un servicio queda `unhealthy` o reinicia | Ejecute `make logs`. Suele ser una clave inválida en `.env` |
| `port is already allocated` | Cambie `*_PORT` en `.env` |
| Error de autenticación de Postgres tras editar `.env` | Ejecute `make reset` para recrear el volumen con la nueva contraseña |
| `network-service` reinicia con `Can't locate revision identified by '…'` | Su volumen tiene migraciones de otra rama o de un experimento. Ejecute `make reset && make up` (borra los datos locales) |
| `make test` imprime solo `OK` sin los pasos `==>` | Tiene el `Makefile` anterior. Haga `git pull` en `main` |

> Todas las copias del proyecto en una misma máquina comparten el nombre de proyecto Compose
> `serviciocerca` y, por tanto, el volumen de la base. Si cambia de rama y la migración ya no
> coincide, use `make reset`.
