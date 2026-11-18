#!/bin/sh
# Prueba de humo de F3 contra la demo levantada (`make up`). Uso: `sh scripts/smoke_f3.sh`.
#
# 1) importa seed/red_demo.json en network-service (replace=true: REEMPLAZA la red de la demo);
# 2) pide a routing-service la ruta de menor costo B_NORTE -> Z_CENTRO (15 min frente a 30);
# 3) comprueba ruta imposible, un solo sentido, la mejor atención (4 ejemplos de docs/05),
#    la traza, los errores del contrato y que network-service rechaza un peso inválido.
# Termina con código distinto de 0 ante la primera falla. Nunca imprime las API keys.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || { echo "FALLA: falta .env (ejecute 'make env')."; exit 1; }

env_value() { grep -E "^$1=" "$ENV_FILE" | tail -n 1 | cut -d= -f2-; }
COORDINATOR_KEY=$(env_value COORDINATOR_API_KEY)
OPERATOR_KEY=$(env_value OPERATOR_API_KEY)
# Igual que Docker Compose: una variable del entorno tiene prioridad sobre .env.
NETWORK_PORT=${NETWORK_PORT:-$(env_value NETWORK_PORT)}
ROUTING_PORT=${ROUTING_PORT:-$(env_value ROUTING_PORT)}
NETWORK_API="http://127.0.0.1:${NETWORK_PORT:-8001}/api/v1"
ROUTING_API="http://127.0.0.1:${ROUTING_PORT:-8002}/api/v1"
BODY=$(mktemp)
trap 'rm -f "$BODY"' EXIT

ok() { echo "  OK    $1"; }
fail() { echo "  FALLA $1"; echo "        respuesta: $(cat "$BODY")"; exit 1; }

# request <url> <método> <api-key> [archivo-json] -> imprime el código HTTP; el cuerpo queda en $BODY
request() {
    if [ $# -eq 4 ]; then
        curl -sS -o "$BODY" -w '%{http_code}' -X "$2" -H "X-API-Key: $3" \
            -H 'Content-Type: application/json' --data-binary "@$4" "$1"
    else
        curl -sS -o "$BODY" -w '%{http_code}' -X "$2" -H "X-API-Key: $3" "$1"
    fi
}

echo "==> smoke F3 contra $ROUTING_API"

code=$(request "$NETWORK_API/network/import" POST "$COORDINATOR_KEY" "$ROOT/seed/red_demo.json")
[ "$code" = 201 ] || fail "importar seed/red_demo.json (HTTP $code)"
ok "importar seed/red_demo.json -> 201"

code=$(request "$ROUTING_API/routes/cheapest?origin=B_NORTE&destination=Z_CENTRO" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"path":\["B_NORTE","Z_ALAMEDA","Z_BOSQUE","Z_CENTRO"\]' "$BODY"     && grep -q '"total_cost":15.0' "$BODY"     && grep -q '"fewest_hops":{"path":\["B_NORTE","Z_CENTRO"\],"hops":1,"cost":30.0}' "$BODY"     && grep -q '"edge_id":"E02","from":"B_NORTE","to":"Z_ALAMEDA"' "$BODY"     || fail "ruta B_NORTE -> Z_CENTRO (HTTP $code)"
ok "B_NORTE -> Z_CENTRO: 15 min en 3 tramos (menos tramos cuesta 30)"

code=$(request "$ROUTING_API/routes/cheapest?origin=B_NORTE&destination=Z_FUENTE" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"found":false' "$BODY" && grep -q '"total_cost":null' "$BODY"     || fail "ruta imposible (HTTP $code)"
ok "B_NORTE -> Z_FUENTE: 200 con found=false"

code=$(request "$ROUTING_API/routes/cheapest?origin=B_SUR&destination=Z_ESTACION" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"total_cost":15.0' "$BODY" || fail "ida de un solo sentido (HTTP $code)"
code=$(request "$ROUTING_API/routes/cheapest?origin=Z_ESTACION&destination=Z_DELICIAS" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"found":false' "$BODY" || fail "vuelta de un solo sentido (HTTP $code)"
ok "Z_DELICIAS -> Z_ESTACION es de un solo sentido"

code=$(request "$ROUTING_API/routes/cheapest?origin=B_NORTE&destination=Z_CENTRO&trace=true" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"action":"relax"' "$BODY" && grep -q '"previous":30.0' "$BODY"     || fail "traza de Dijkstra (HTTP $code)"
ok "trace=true devuelve la traza de Dijkstra"

code=$(request "$ROUTING_API/attention/best?zone=Z_COLINA" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"base":"B_SUR"' "$BODY" && grep -q '"total_cost":20.0' "$BODY"     && grep -q '"alternatives":\[{"base":"B_NORTE","total_cost":25.0,"hops":4}\]' "$BODY"     || fail "mejor atención Z_COLINA (HTTP $code)"
ok "Z_COLINA: atender desde B_SUR (20 min; B_NORTE 25)"

code=$(request "$ROUTING_API/attention/best?zone=Z_ESTACION" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"best":{"base":"B_SUR"' "$BODY" && grep -q '"total_cost":15.0' "$BODY"     || fail "mejor atención Z_ESTACION (HTTP $code)"
ok "Z_ESTACION: atender desde B_SUR (15 min)"

code=$(request "$ROUTING_API/attention/best?zone=Z_FUENTE" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"found":false' "$BODY" && grep -q 'sin técnicos disponibles' "$BODY"     || fail "zona solo alcanzable sin técnicos (HTTP $code)"
ok "Z_FUENTE: no atendible, solo la alcanza una base sin técnicos"

code=$(request "$ROUTING_API/attention/best?zone=Z_ISLA" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q 'inalcanzable desde toda base' "$BODY"     || fail "zona inalcanzable (HTTP $code)"
ok "Z_ISLA: inalcanzable desde toda base"

code=$(request "$ROUTING_API/routes/cheapest?origin=B_NADA&destination=Z_CENTRO" GET "$OPERATOR_KEY")
[ "$code" = 404 ] && grep -q '"code":"ORIGIN_NOT_FOUND"' "$BODY" || fail "origen inexistente (HTTP $code)"
code=$(request "$ROUTING_API/routes/cheapest?origin=B_NORTE&destination=Z_NADA" GET "$OPERATOR_KEY")
[ "$code" = 404 ] && grep -q '"code":"DESTINATION_NOT_FOUND"' "$BODY" || fail "destino inexistente (HTTP $code)"
code=$(request "$ROUTING_API/attention/best?zone=Z_NADA" GET "$OPERATOR_KEY")
[ "$code" = 404 ] && grep -q '"code":"ZONE_NOT_FOUND"' "$BODY" || fail "zona inexistente (HTTP $code)"
ok "inexistentes -> 404 ORIGIN_NOT_FOUND, DESTINATION_NOT_FOUND y ZONE_NOT_FOUND"

BAD_EDGE=$(mktemp)
trap 'rm -f "$BODY" "$BAD_EDGE"' EXIT
printf '%s' '{"id":"E_SMOKE","source":"B_NORTE","target":"Z_ISLA","weight":-5}' > "$BAD_EDGE"
code=$(request "$NETWORK_API/edges" POST "$COORDINATOR_KEY" "$BAD_EDGE")
[ "$code" = 422 ] && grep -q '"code":"INVALID_WEIGHT"' "$BODY" || fail "peso -5 (HTTP $code)"
ok "conexión con peso -5 -> 422 INVALID_WEIGHT"

code=$(request "$ROUTING_API/attention/best?zone=Z_COLINA" GET "")
[ "$code" = 401 ] || fail "sin clave debe dar 401 (HTTP $code)"
ok "sin X-API-Key -> 401"

echo "OK: smoke F3 en verde"
