#!/bin/sh
# Harness de calidad del servicio. Debe terminar en verde para considerar una tarea "hecha".
set -eu

echo "==> eslint (lint)";          npx eslint . --max-warnings 0
echo "==> prettier (formato)";     npx prettier --check .
echo "==> tsc (tipos)";            npm run --silent typecheck
echo "==> npm audit (CVEs)"
# App publicada (dependencias de producción, las que van en la imagen runtime): sin excepciones.
npm audit --omit=dev
# Herramientas de desarrollo: EXCEPCIÓN TEMPORAL. picomatch (GHSA-fc5q-39xc-vjpf, alto) no tiene
# versión corregida publicada y solo lo usan Vite/Vitest; aquí se bloquea únicamente lo crítico.
# Volver a `npm audit` sin opciones cuando salga el arreglo (docs/07-testing-y-harness.md).
npm audit --audit-level=critical
echo "==> vitest";                 npx vitest run --coverage
