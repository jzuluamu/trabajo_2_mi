"""Genera `.env` a partir de `.env.example` reemplazando cada valor CHANGE_ME_* por un secreto.

Uso: `make env` (se ejecuta dentro de un contenedor Python; no requiere Python local).
"""

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE, TARGET = ROOT / ".env.example", ROOT / ".env"
PLACEHOLDER = "CHANGE_ME"


def render(example: str) -> str:
    lines = []
    for line in example.splitlines():
        key, sep, value = line.partition("=")
        if sep and not line.lstrip().startswith("#") and value.startswith(PLACEHOLDER):
            line = f"{key}={secrets.token_urlsafe(32)}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def main() -> int:
    if TARGET.exists():
        print(".env ya existe; no se sobrescribe. Bórrelo manualmente si quiere regenerarlo.")
        return 0
    TARGET.write_text(render(EXAMPLE.read_text()))
    print(".env generado con secretos aleatorios. Sus API keys están en .env (no se versiona).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
