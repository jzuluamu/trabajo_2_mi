#!/bin/sh
# Aceptación de los 4 escenarios del brief (Feature 4) contra la demo levantada (`make up`).
# Uso: `make test-acceptance` (o `sh scripts/acceptance.sh` en Git Bash/WSL).
#
# Todo pasa por la CONSOLA WEB (BFF en :8080), con cookie de sesión y el encabezado anti-CSRF,
# igual que un coordinador y un operador en el navegador:
#   1. Éxito: el coordinador registra la red; el operador consulta una zona y recibe una
#      alternativa entendible (cobertura, ruta de menor costo y mejor base).
#   2. Zona inexistente: errores del contrato (404), legibles y sin reflejar la entrada.
#   3. Red desconectada: respuestas válidas (200) con found=false / covered=false, no errores.
#   4. Peso inválido: 0, -5 y 1441 se rechazan con INVALID_WEIGHT y la red no cambia.
# REEMPLAZA la red de la demo por seed/red_demo.json. Nunca imprime las API keys.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || { echo "FALLA: falta .env (ejecute 'make env')."; exit 1; }

env_value() { grep -E "^$1=" "$ENV_FILE" | tail -n 1 | cut -d= -f2-; }
# Igual que Docker Compose: una variable del entorno tiene prioridad sobre .env.
WEB_PORT=${WEB_PORT:-$(env_value WEB_PORT)}
WEB="http://127.0.0.1:${WEB_PORT:-8080}"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
BODY="$TMP/body.json"

ok() { echo "  OK    $1"; }
fail() { echo "  FALLA $1"; echo "        respuesta: $(cat "$BODY")"; exit 1; }

# call <jar> <método> <ruta> [archivo-json] -> imprime el código HTTP; el cuerpo queda en $BODY
call() {
    if [ $# -eq 4 ]; then
        curl -sS -o "$BODY" -w '%{http_code}' -b "$1" -c "$1" -X "$2" \
            -H 'X-ServicioCerca: 1' -H 'Content-Type: application/json' \
            --data-binary "@$4" "$WEB$3"
    else
        curl -sS -o "$BODY" -w '%{http_code}' -b "$1" -c "$1" -X "$2" \
            -H 'X-ServicioCerca: 1' "$WEB$3"
    fi
}

# login <jar> <variable del .env> <rol esperado>: la clave va en un archivo, no en la línea de comandos.
login() {
    printf '{"api_key":"%s"}' "$(env_value "$2")" > "$TMP/key.json"
    code=$(call "$1" POST /bff/session "$TMP/key.json")
    rm -f "$TMP/key.json"
    [ "$code" = 200 ] && grep -q "\"role\":\"$3\"" "$BODY" || fail "inicio de sesión como $3 (HTTP $code)"
}

COORD="$TMP/coordinador.cookies"
OPER="$TMP/operador.cookies"
R=/bff/api/routing
N=/bff/api/network

echo "==> aceptación F4 contra la consola web $WEB"

echo "Escenario 1 · Éxito"
login "$COORD" COORDINATOR_API_KEY coordinator
code=$(call "$COORD" POST "$N/network/import" "$ROOT/seed/red_demo.json")
[ "$code" = 201 ] && grep -q '"nodes":11' "$BODY" && grep -q '"edges":9' "$BODY" \
    || fail "el coordinador registra la red (HTTP $code)"
ok "el coordinador registra la red: 11 lugares y 9 conexiones"
login "$OPER" OPERATOR_API_KEY operator
code=$(call "$OPER" GET "$R/coverage?base=B_NORTE&zone=Z_CENTRO")
[ "$code" = 200 ] && grep -q '"covered":true' "$BODY" || fail "cobertura de Z_CENTRO (HTTP $code)"
ok "el operador consulta la zona Centro: cubierta desde Base Norte en 1 tramo"
code=$(call "$OPER" GET "$R/routes/cheapest?origin=B_NORTE&destination=Z_CENTRO")
# Por el BFF los números llegan como JSON de JavaScript: 15 (sin ".0").
[ "$code" = 200 ] && grep -Eq '"total_cost":15(\.0)?,' "$BODY" \
    && grep -q '"path":\["B_NORTE","Z_ALAMEDA","Z_BOSQUE","Z_CENTRO"\]' "$BODY" \
    && grep -Eq '"fewest_hops":\{"path":\["B_NORTE","Z_CENTRO"\],"hops":1,"cost":30(\.0)?\}' "$BODY" \
    || fail "ruta de menor costo (HTTP $code)"
ok "ruta más rápida Base Norte -> Centro: 15 min por Alameda y Bosque (el directo tarda 30)"
code=$(call "$OPER" GET "$R/attention/best?zone=Z_COLINA")
[ "$code" = 200 ] && grep -q '"best":{"base":"B_SUR","technicians":\[{"id":"T03","name":"Marta"}\]' "$BODY" \
    && grep -q '"message":"Atender desde B_SUR (Marta): 20 min."' "$BODY" \
    || fail "mejor base para Z_COLINA (HTTP $code)"
ok "alternativa entendible para Colina: \"Atender desde B_SUR (Marta): 20 min.\""

echo "Escenario 2 · Zona inexistente"
code=$(call "$OPER" GET "$R/coverage?base=B_NORTE&zone=Z_NO_EXISTE")
[ "$code" = 404 ] && grep -q '"code":"ZONE_NOT_FOUND"' "$BODY" || fail "cobertura de zona inexistente (HTTP $code)"
ok "cobertura -> 404 ZONE_NOT_FOUND"
code=$(call "$OPER" GET "$R/attention/best?zone=Z_NO_EXISTE")
[ "$code" = 404 ] && grep -q '"code":"ZONE_NOT_FOUND"' "$BODY" || fail "mejor base de zona inexistente (HTTP $code)"
ok "mejor base -> 404 ZONE_NOT_FOUND"
code=$(call "$OPER" GET "$R/routes/cheapest?origin=B_NORTE&destination=Z_NO_EXISTE")
[ "$code" = 404 ] && grep -q '"code":"DESTINATION_NOT_FOUND"' "$BODY" || fail "ruta a zona inexistente (HTTP $code)"
ok "ruta -> 404 DESTINATION_NOT_FOUND"
code=$(call "$OPER" GET "$R/coverage?base=B_NORTE&zone=z%3Cscript%3E")
[ "$code" = 422 ] && grep -q '"code":"VALIDATION_ERROR"' "$BODY" && ! grep -q 'script' "$BODY" \
    || fail "id mal formado (HTTP $code)"
ok "id mal formado -> 422 VALIDATION_ERROR sin reflejar la entrada"

echo "Escenario 3 · Red desconectada"
code=$(call "$OPER" GET "$R/coverage?base=B_NORTE&zone=Z_FUENTE")
[ "$code" = 200 ] && grep -q '"covered":false' "$BODY" \
    && grep -q '"unreachable_zones":\["Z_FUENTE","Z_ISLA"\]' "$BODY" || fail "cobertura de Z_FUENTE (HTTP $code)"
ok "Fuente e Isla quedan sin cobertura desde Base Norte: 200 con covered=false"
code=$(call "$OPER" GET "$R/routes/cheapest?origin=B_NORTE&destination=Z_FUENTE")
[ "$code" = 200 ] && grep -q '"found":false' "$BODY" && grep -q '"path":\[\]' "$BODY" \
    || fail "ruta a otra componente (HTTP $code)"
ok "ruta Base Norte -> Fuente: 200 con found=false, sin error"
code=$(call "$OPER" GET "$R/attention/best?zone=Z_FUENTE")
[ "$code" = 200 ] && grep -q '"found":false' "$BODY" \
    && grep -q 'solo es alcanzable desde bases sin técnicos disponibles (B_OESTE)' "$BODY" \
    || fail "mejor base para Z_FUENTE (HTTP $code)"
ok "Fuente: alcanzable solo por una base sin técnicos -> no atendible, con su motivo"
code=$(call "$OPER" GET "$R/attention/best?zone=Z_ISLA")
[ "$code" = 200 ] && grep -q '"found":false' "$BODY" && grep -q 'inalcanzable desde toda base' "$BODY" \
    || fail "mejor base para Z_ISLA (HTTP $code)"
ok "Isla: inalcanzable desde toda base, con su motivo"

echo "Escenario 4 · Peso inválido"
for weight in -5 0 1441; do
    printf '{"id":"E_ACEPT","source":"B_NORTE","target":"Z_ISLA","weight":%s,"bidirectional":true}' \
        "$weight" > "$TMP/edge.json"
    code=$(call "$COORD" POST "$N/edges" "$TMP/edge.json")
    [ "$code" = 422 ] && grep -q '"code":"INVALID_WEIGHT"' "$BODY" || fail "peso $weight (HTTP $code)"
done
ok "pesos -5, 0 y 1441 -> 422 INVALID_WEIGHT con mensaje legible"
code=$(call "$COORD" GET "$N/network")
[ "$code" = 200 ] && ! grep -q 'E_ACEPT' "$BODY" || fail "la red no debía cambiar (HTTP $code)"
ok "la red sigue intacta: no se guardó ninguna conexión inválida"

call "$COORD" DELETE /bff/session >/dev/null
call "$OPER" DELETE /bff/session >/dev/null
echo "OK: aceptación F4 en verde (4 escenarios)"
