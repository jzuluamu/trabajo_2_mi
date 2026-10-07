#!/bin/sh
# Prueba de humo de F1 contra la demo levantada (`make up`). Uso: `make smoke-f1`.
#
# 1) importa seed/red_demo.json (replace=true: REEMPLAZA la red actual de la demo);
# 2) lee la red y comprueba 11 nodos y 9 conexiones;
# 3) provoca INVALID_WEIGHT con peso -5;
# 4) reinicia network-service y comprueba que la red persiste en PostgreSQL.
# Termina con código distinto de 0 ante la primera falla. Nunca imprime las API keys.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || { echo "FALLA: falta .env (ejecute 'make env')."; exit 1; }

env_value() { grep -E "^$1=" "$ENV_FILE" | tail -n 1 | cut -d= -f2-; }
COORDINATOR_KEY=$(env_value COORDINATOR_API_KEY)
OPERATOR_KEY=$(env_value OPERATOR_API_KEY)
# Igual que Docker Compose: una variable del entorno tiene prioridad sobre .env.
PORT=${NETWORK_PORT:-$(env_value NETWORK_PORT)}
API="http://127.0.0.1:${PORT:-8001}/api/v1"
BODY=$(mktemp)
trap 'rm -f "$BODY"' EXIT

ok() { echo "  OK    $1"; }
fail() { echo "  FALLA $1"; echo "        respuesta: $(cat "$BODY")"; exit 1; }

# request <método> <ruta> <api-key> [archivo-json] -> imprime el código HTTP; el cuerpo queda en $BODY
request() {
    if [ $# -eq 4 ]; then
        curl -sS -o "$BODY" -w '%{http_code}' -X "$1" -H "X-API-Key: $3" \
            -H 'Content-Type: application/json' --data-binary "@$4" "$API$2"
    else
        curl -sS -o "$BODY" -w '%{http_code}' -X "$1" -H "X-API-Key: $3" "$API$2"
    fi
}

count() { grep -o "\"$1\":" "$BODY" | wc -l | tr -d ' '; }

echo "==> smoke F1 contra $API"

code=$(request POST /network/import "$COORDINATOR_KEY" "$ROOT/seed/red_demo.json")
[ "$code" = 201 ] && grep -q '"nodes":11' "$BODY" && grep -q '"edges":9' "$BODY" \
    || fail "importar seed/red_demo.json (HTTP $code)"
ok "importar seed/red_demo.json -> 201 {nodes: 11, edges: 9}"

code=$(request GET /network "$OPERATOR_KEY")
[ "$code" = 200 ] && [ "$(count type)" = 11 ] && [ "$(count bidirectional)" = 9 ] \
    || fail "leer la red como operador (HTTP $code)"
cp "$BODY" "$BODY.before"
trap 'rm -f "$BODY" "$BODY.before"' EXIT
ok "leer la red (operador) -> 11 nodos y 9 conexiones"

WEIGHT=$(mktemp)
printf '%s' '{"id":"E_SMOKE","source":"Z_ISLA","target":"Z_FUENTE","weight":-5}' > "$WEIGHT"
code=$(request POST /edges "$COORDINATOR_KEY" "$WEIGHT")
rm -f "$WEIGHT"
[ "$code" = 422 ] && grep -q '"code":"INVALID_WEIGHT"' "$BODY" \
    || fail "peso -5 debe dar INVALID_WEIGHT (HTTP $code)"
ok "peso -5 -> 422 INVALID_WEIGHT"

echo "  ...   reiniciando network-service"
docker compose -f "$ROOT/docker-compose.yml" restart network-service >/dev/null 2>&1
docker compose -f "$ROOT/docker-compose.yml" up -d --wait network-service >/dev/null 2>&1 \
    || { echo "  FALLA network-service no volvió a estar healthy"; exit 1; }
code=$(request GET /network "$OPERATOR_KEY")
[ "$code" = 200 ] && cmp -s "$BODY" "$BODY.before" \
    || fail "la red debe persistir tras reiniciar (HTTP $code)"
ok "tras reiniciar network-service la red es idéntica (persistencia en PostgreSQL)"

echo "OK: smoke F1 en verde"
