#!/bin/sh
# Prueba de humo de F2 contra la demo levantada (`make up`). Uso: `make smoke-f2`.
#
# 1) importa seed/red_demo.json en network-service (replace=true: REEMPLAZA la red de la demo);
# 2) pide a routing-service la cobertura de B_NORTE (alcanza 6 nodos y 2 zonas quedan sin cobertura);
# 3) comprueba una zona cubierta, una no cubierta, la traza y los errores del contrato.
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

echo "==> smoke F2 contra $ROUTING_API"

code=$(request "$NETWORK_API/network/import" POST "$COORDINATOR_KEY" "$ROOT/seed/red_demo.json")
[ "$code" = 201 ] || fail "importar seed/red_demo.json (HTTP $code)"
ok "importar seed/red_demo.json -> 201"

code=$(request "$ROUTING_API/coverage?base=B_NORTE" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"unreachable_zones":\["Z_FUENTE","Z_ISLA"\]' "$BODY" \
    && grep -q '{"node_id":"Z_ALAMEDA","type":"ZONE","hops":1}' "$BODY" \
    && grep -q '"zone":null' "$BODY" && grep -q '"trace":null' "$BODY" \
    || fail "cobertura de B_NORTE (HTTP $code)"
ok "cobertura de B_NORTE -> Z_FUENTE y Z_ISLA sin cobertura"

code=$(request "$ROUTING_API/coverage?base=B_NORTE&zone=Z_CENTRO" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"covered":true' "$BODY" && grep -q '"hops":1' "$BODY" \
    || fail "zona cubierta Z_CENTRO (HTTP $code)"
ok "Z_CENTRO cubierta desde B_NORTE en 1 tramo"

code=$(request "$ROUTING_API/coverage?base=B_NORTE&zone=Z_FUENTE" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"covered":false' "$BODY" \
    || fail "zona no cubierta Z_FUENTE (HTTP $code)"
ok "Z_FUENTE no cubierta -> 200 con covered=false"

code=$(request "$ROUTING_API/coverage?base=B_NORTE&trace=true" GET "$OPERATOR_KEY")
[ "$code" = 200 ] && grep -q '"action":"visit"' "$BODY" \
    || fail "traza (HTTP $code)"
ok "trace=true devuelve la traza del BFS"

code=$(request "$ROUTING_API/coverage?base=B_NADA" GET "$OPERATOR_KEY")
[ "$code" = 404 ] && grep -q '"code":"ORIGIN_NOT_FOUND"' "$BODY" \
    || fail "origen inexistente (HTTP $code)"
ok "base inexistente -> 404 ORIGIN_NOT_FOUND"

code=$(request "$ROUTING_API/coverage?base=Z_CENTRO" GET "$OPERATOR_KEY")
[ "$code" = 422 ] && grep -q '"code":"INVALID_ORIGIN"' "$BODY" \
    || fail "origen que no es base (HTTP $code)"
ok "origen de tipo zona -> 422 INVALID_ORIGIN"

code=$(request "$ROUTING_API/coverage?base=B_NORTE&zone=Z_NADA" GET "$OPERATOR_KEY")
[ "$code" = 404 ] && grep -q '"code":"ZONE_NOT_FOUND"' "$BODY" \
    || fail "zona inexistente (HTTP $code)"
ok "zona inexistente -> 404 ZONE_NOT_FOUND"

code=$(request "$ROUTING_API/coverage?base=B_NORTE" GET "")
[ "$code" = 401 ] || fail "sin clave debe dar 401 (HTTP $code)"
ok "sin X-API-Key -> 401"

echo "OK: smoke F2 en verde"
