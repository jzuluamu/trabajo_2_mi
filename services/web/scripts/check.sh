#!/bin/sh
# Harness de calidad del servicio. Debe terminar en verde para considerar una tarea "hecha".
set -eu

echo "==> eslint (lint)";          npx eslint . --max-warnings 0
echo "==> prettier (formato)";     npx prettier --check .
echo "==> tsc (tipos)";            npm run --silent typecheck
echo "==> npm audit (CVEs)";       npm audit
echo "==> vitest";                 npx vitest run --coverage
