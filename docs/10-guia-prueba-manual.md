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

5. Compruebe que `db`, `network-service`, `routing-service`, `console` y `web` estén `Up (healthy)`, y que ninguno quede en `Restarting`:

   ```bash
   docker compose ps
   ```

6. Ejecute el harness:

   ```bash
   make test
   ```

   Debe ver, **por cada servicio**, los pasos del harness (`==> ruff … ==> pytest` en Python y `==> eslint … ==> vitest` en la consola web) y `N passed`. Al final debe aparecer `OK: harness en verde para: network routing console web`. Si solo aparece `OK`, sin esos pasos, su copia está desactualizada: haga `git pull`.

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
| `NETWORK_PORT`, `ROUTING_PORT`, `CONSOLE_PORT`, `WEB_PORT` | Solo si el puerto está ocupado | Por defecto 8001, 8002, 8501 y 8080. `WEB_PORT` es nueva (consola web); si su `.env` no la tiene, se usa 8080 |
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

   Esperado: `db`, `network-service`, `routing-service`, `console` y `web` en estado `healthy`.

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

   Esperado: `OK: harness en verde para: network routing console web`.

9. **Apagar:**

   ```bash
   make down
   ```

   O `make reset` para borrar también los datos.

## F1 · Red de cobertura

> `make smoke-f1` y "Cargar red" con *Reemplazar la red actual* **sustituyen** la red de su demo
> por la de `seed/red_demo.json`.

1. **Base limpia y migración:**

   ```bash
   make reset && make up
   ```

   ```bash
   docker compose logs network-service | grep upgrade
   ```

   Esperado: `Running upgrade  -> 0001`.

2. **Harness y humo:**

   ```bash
   make test
   ```

   ```bash
   make smoke-f1
   ```

   Esperado: `OK: harness en verde…` y `OK: smoke F1 en verde`, con los cuatro pasos en `OK`: importar, leer, `INVALID_WEIGHT` y persistencia tras reiniciar.

3. **Swagger:** abra <http://localhost:8001/docs>. Debe listar las 9 rutas de nodos, conexiones y red.

4. **Consola como operador:** abra <http://localhost:8501>, pegue `OPERATOR_API_KEY`, pulse Enter y luego "Ingresar".
   1. La consola es clara (fondo azul muy pálido). Verá los indicadores: 3 bases (2 con técnico libre), 8 zonas, 9 trayectos (1 de un solo sentido) y 1 zona sin conexión.
   2. El **mapa** muestra las bases como cuadrados azules (Base Oeste más pálida, "sin técnicos libres"), las zonas como círculos, Isla con borde punteado ("sin conexión"), los minutos en cada trayecto y una flecha en Delicias → Estación.
   3. Arrastre un nodo: se queda donde lo suelta. Use la rueda o "+"/"−" para el zoom y "Ajustar" para volver a ver todo. Pase el mouse sobre un nodo para ver su resumen.
   4. Haga clic en Centro: se resaltan sus trayectos y el resto se atenúa. Clic en el fondo: todo vuelve a la normalidad.
   5. En **Ficha de**, elija Base Norte: verá a Ana "Disponible" y a Luis "No disponible", y sus trayectos. Elija Base Oeste: verá el aviso "Base sin técnicos disponibles…".
   6. "Ver como tabla (accesible)" muestra las mismas bases, zonas y conexiones en tablas.
   7. No aparece la pestaña "Configurar red": el operador solo lee.

5. **Consola como coordinador:** cierre sesión y entre con `COORDINATOR_API_KEY`. Abra la pestaña **Configurar red** y use "¿Qué desea hacer?" para elegir la acción.
   1. *Registrar nodo*: Tipo **Base**, ID `B_ESTE`, Nombre `Base Este`, Técnicos `T10; Sara; sí`. Verá "Nodo 'B_ESTE' registrado." y el nodo en la tabla.
   2. Repita con el ID `B_ESTE`: verá "Ya existe un nodo con id 'B_ESTE'.".
   3. *Registrar conexión*: ID `E10`, Desde `B_ESTE`, Hasta `Z_ISLA`, Minutos `-5`. Antes de guardar, el mapa dibuja la conexión punteada en rojo con "revisar". Pulse "Registrar conexión": verá el mensaje de `INVALID_WEIGHT`: "El peso de la conexión 'E10' debe ser mayor que 0 y menor o igual a 1440 minutos.". Cambie a `12`: la vista previa pasa a ámbar con "12 min · vista previa". Registre: verá "Conexión 'E10' registrada." y el trayecto en el mapa.
   4. *Eliminar*: elija el nodo `B_ESTE` y pulse "Eliminar nodo". Verá que tiene conexiones (`NODE_IN_USE`). Elimine primero la conexión `E10` y después el nodo.
   5. *Cargar red*: suba `seed/red_demo.json`, deje marcado "Reemplazar la red actual" y pulse "Cargar red". Verá "Red cargada: 11 nodos y 9 conexiones.".

6. **Permisos por API:**

   ```bash
   curl -i -X POST -H "X-API-Key: <OPERATOR_API_KEY>" -H "Content-Type: application/json" -d '{"id":"Z_X","type":"ZONE","name":"X"}' http://localhost:8001/api/v1/nodes
   ```

   Esperado: `403` con `FORBIDDEN`.

7. **Persistencia:**

   ```bash
   make down && make up
   ```

   Recargue la consola: la red sigue ahí.

## F2 · Consulta de cobertura

> `make smoke-f2` y "Cargar red" con *Reemplazar la red actual* **sustituyen** la red de su demo
> por la de `seed/red_demo.json`. No hay variables nuevas en `.env`.

1. **Levante la demo con la red demo cargada:**

   ```bash
   make reset && make up
   ```

   Entre a la consola como coordinador, abra **Configurar red** y cargue `seed/red_demo.json` (o ejecute `make smoke-f2`, que también la importa).

2. **Harness y humo:**

   ```bash
   make test
   ```

   ```bash
   make smoke-f2
   ```

   Esperado: `OK: smoke F2 en verde`, con los nueve pasos en `OK`.

3. **Swagger:** abra <http://localhost:8002/docs>. Debe listar `GET /api/v1/coverage`.

4. **API con `curl`** (use `OPERATOR_API_KEY` de su `.env`):

   ```bash
   curl -s -H "X-API-Key: <OPERATOR_API_KEY>" "http://localhost:8002/api/v1/coverage?base=B_NORTE&zone=Z_CENTRO"
   ```

   Esperado: `Z_CENTRO` cubierta en 1 tramo y `unreachable_zones` con `Z_FUENTE` y `Z_ISLA`. Con `&trace=true` aparece la traza de 16 entradas de [04](04-algoritmos-bfs.md). Con `base=B_NADA` responde `404 ORIGIN_NOT_FOUND`; con `base=Z_CENTRO`, `422 INVALID_ORIGIN`; con `zone=Z_NADA`, `404 ZONE_NOT_FOUND`; sin clave, `401`.

5. **Consola:** abra <http://localhost:8501>, entre como operador o coordinador y abra la pestaña **Cobertura**.
   1. Elija **Base Norte** y pulse "Consultar cobertura": verá 2 indicadores (7 nodos alcanzables sin contar la base, que son 6 zonas y Base Sur, y 2 zonas sin cobertura) y la tabla de tramos mínimos (Alameda y Centro a 1 tramo).
   2. Elija la zona **Centro** y consulte: aparece en verde "Z_CENTRO está cubierta desde B_NORTE (1 tramo).".
   3. Elija la zona **Fuente**: aparece en ámbar que no hay conexión, y no es un error. Fuente e Isla figuran en "Zonas sin cobertura".
   4. Marque "Mostrar traza paso a paso" y consulte: el desplegable "Traza del recorrido BFS" muestra el paso a paso.
   5. Elija **Base Sur** y la zona **Estación**: está cubierta a 2 tramos (Sur → Delicias → Estación). El trayecto Delicias → Estación es de un solo sentido, pero se recorre en esa dirección.

6. **Servicio caído:** detenga network-service (`docker compose stop network-service`) y consulte la cobertura por `curl`: responde `503 NETWORK_UNAVAILABLE` sin detalles técnicos. Vuelva a levantarlo con `make up`.

## Consola web (React)

> Consola nueva ([ADR 0007](adr/0007-consola-web-react-bff.md)) en <http://localhost:8080>. Convive con
> Streamlit (<http://localhost:8501>) hasta que este recorrido pase completo. No hace falta cambiar
> `.env`: `WEB_PORT` es opcional (8080 por defecto).

1. **Levantar y verificar:**

   ```bash
   make up
   ```

   ```bash
   make test-web
   ```

   Esperado: `web` aparece *healthy* en `make ps`, y `make test-web` termina con `Tests N passed` y la cobertura ≥ 85 %.

2. **La clave no llega al navegador:** abra <http://localhost:8080>, pegue `OPERATOR_API_KEY` en "Clave de acceso" y pulse "Entrar". En las herramientas del navegador (*Application → Cookies*) verá solo `sc_session` (`HttpOnly`, `SameSite=Strict`) con un valor aleatorio, distinto de su clave. En *Local Storage* solo aparece `sc-theme` (el tema).

3. **Inicio de sesión:**
   1. Una clave incorrecta muestra "API key inválida." bajo el campo.
   2. `INTERNAL_API_KEY` muestra "Esta clave no corresponde a un usuario de la consola.".
   3. El operador ve las pestañas **Red** y **Cobertura**. El coordinador ve además **Configurar red**.
   4. La cabecera dice "Todo en línea".

4. **Red** (con la red demo cargada):
   1. La interfaz es blanca y gris, y el mapa abre completo, sin resaltado.
   2. Indicadores: 3 bases (2 con técnico libre), 8 zonas (7 con trayectos), 9 trayectos (1 de un solo sentido) y 1 zona sin conexión.
   3. **Haga clic en Isla en el mapa:** el detalle cambia a "Isla" con el aviso "Sin trayectos registrados…" y el mapa resalta Isla en azul. Haga clic en el fondo: se quita el resaltado.
   4. En "Ver detalle de" elija **Estación**: su trayecto dice "solo llegada (desde allá)".
   5. Pase el mouse sobre el trayecto Delicias → Estación: "Delicias → Estación · 7 min · solo ida (E08)".
   6. Arrastre un nodo, cambie a **Cobertura** y vuelva: el nodo sigue donde lo dejó.
   7. "Ver como tabla (accesible)" muestra las mismas bases, zonas y conexiones.

5. **Cobertura:**
   1. Base de partida "Base Norte", "¿Revisar una zona en particular?" → **Fuente**, y "Ver cobertura". Arriba aparece "Base Norte llega a 6 zonas y 1 base. Quedan sin cobertura Fuente e Isla.", y en ámbar "Fuente no está cubierta / No hay ningún camino desde Base Norte hasta Fuente.".
   2. En el mapa, Base Norte es el origen (azul con anillo ámbar), cada lugar alcanzado se pinta de azul y dice "N tramos", y Fuente e Isla dicen "sin cobertura". Base Oeste queda atenuada.
   3. "Lugares a su alcance" agrupa por distancia: "A 1 tramo: Alameda, Centro"… "A 4 tramos: Base Sur, Estación".
   4. Con "Incluir el recorrido paso a paso", el botón "Ver el recorrido paso a paso (16 pasos)" despliega la traza con nombres.
   5. "¿Cómo se calcula?" explica la regla.

6. **Configurar red** (coordinador):
   1. *Nueva base o zona*: deje "Base", escriba el nombre `Base Este` y verá el identificador `B_ESTE` ya propuesto. Escriba `Sara` como técnico 1 y pulse "Agregar base": aparece "Listo: se agregó Base Este.".
   2. Repita con el nombre `Base Este`: el identificador propuesto pasa a `B_ESTE_2`. Cámbielo a `B_ESTE` y pulse "Agregar base": verá "Ya existe un nodo con id 'B_ESTE'.".
   3. *Nueva conexión*: Desde "Base Este", Hasta "Isla", minutos `-5`. El identificador propuesto es `E10`. Antes de guardar, el mapa dibuja la línea punteada roja con "revisar". Pulse "Guardar conexión": verá el mensaje de `INVALID_WEIGHT`. Cambie a `12`: la vista previa pasa a ámbar. Guarde: "Listo: se conectó Base Este con Isla (12 min).".
   4. *Eliminar*: elija el lugar "Base Este". Verá "Antes elimine su conexión: Base Este ↔ Isla · 12 min." y el botón deshabilitado. Elimine esa conexión (con confirmación) y luego el lugar.
   5. *Cargar archivo*: arrastre `seed/red_demo.json` al área (o haga clic para elegirlo), deje "Reemplazar todo" y pulse "Cargar red": "Red cargada: 11 lugares y 9 conexiones.".

7. **Tema y móvil:**
   1. El botón del sol o la luna cambia entre claro, oscuro y "Según el sistema". El mapa cambia de paleta y la preferencia se recuerda al recargar.
   2. Con el navegador a 375 px de ancho (modo dispositivo), no hay desplazamiento horizontal, el estado del sistema aparece bajo la cabecera y los controles del mapa quedan en una fila.

8. **Caída de un servicio:**

   ```bash
   docker compose stop routing-service
   ```

   En la cabecera, "Consultas: sin conexión" aparece en menos de 15 s. Una consulta de cobertura muestra "No fue posible contactar routing-service." sin romper la página. Vuelva a levantarlo:

   ```bash
   docker compose start routing-service
   ```

## Fases posteriores (fuera del alcance actual)

Se completan al cerrar cada fase (ver [09](09-fases-y-roadmap.md)). Recorrido previsto para la demo final:
- cargar la red demo;
- consultar la ruta `B_NORTE → Z_CENTRO` (15 min, contra 30 por el camino de menos tramos);
- consultar la mejor atención para `Z_COLINA` (B_SUR) y para `Z_FUENTE` (no atendible);
- probar una zona inexistente;
- intentar registrar una conexión con peso `-5`, que debe rechazarse con `INVALID_WEIGHT`.

## Problemas comunes

| Síntoma | Causa probable / solución |
|---|---|
| `Falta .env` | Ejecute `make env` |
| Un servicio queda `unhealthy` o reinicia | Ejecute `make logs`. Suele ser una clave inválida en `.env` |
| `port is already allocated` | Cambie `*_PORT` en `.env` (o detenga la otra copia del proyecto que usa esos puertos) |
| La consola web pide iniciar sesión otra vez tras `make up` | Es lo esperado: las sesiones del BFF viven en memoria y se pierden al reconstruir el contenedor `web` |
| Error de autenticación de Postgres tras editar `.env` | Ejecute `make reset` para recrear el volumen con la nueva contraseña |
| `network-service` reinicia con `Can't locate revision identified by '…'` | Su volumen tiene migraciones de otra rama o de un experimento. Ejecute `make reset && make up` (borra los datos locales) |
| `make test` imprime solo `OK` sin los pasos `==>` | Tiene el `Makefile` anterior. Haga `git pull` en `main` |

> Todas las copias del proyecto en una misma máquina comparten el nombre de proyecto Compose
> `serviciocerca` y, por tanto, el volumen de la base. Si cambia de rama y la migración ya no
> coincide, use `make reset`.
