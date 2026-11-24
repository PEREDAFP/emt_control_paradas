#!/usr/bin/env python3
"""Muestra en pantalla las paradas de una línea de EMT Madrid.

Uso:
    python3 src/mostrar_paradas.py [line_id] [direccion]

Ejemplos:
    python3 src/mostrar_paradas.py 86        # dirección 1 (ida)
    python3 src/mostrar_paradas.py 86 2      # dirección 2 (vuelta)
"""

import sys
from typing import Any, Dict, List, Optional

try:
    from .config import EMT_EMAIL, EMT_PASSWORD
    from .api_client import EMTClient, EMTApiError
except ImportError:  # Ejecución directa como script
    from config import EMT_EMAIL, EMT_PASSWORD
    from api_client import EMTClient, EMTApiError

LINE_ID_DEFAULT = "86"
DIRECTION_DEFAULT = "1"


def _formatear_parada(p: Dict[str, Any]) -> str:
    codigo = p.get("stop") or p.get("id") or p.get("codigo") or p.get("stopId") or "-"
    nombre = p.get("name") or p.get("nombre") or "-"
    direccion = p.get("postalAddress") or p.get("address") or p.get("direccion") or "-"
    return f"  {codigo:<8} | {nombre:<40} | {direccion}"


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    line_id = argv[0] if len(argv) > 0 else LINE_ID_DEFAULT
    direction = argv[1] if len(argv) > 1 else DIRECTION_DEFAULT

    if not EMT_EMAIL or not EMT_PASSWORD:
        print("Faltan credenciales: configura EMT_EMAIL y EMT_PASSWORD en .env")
        return 1

    client = EMTClient(email=EMT_EMAIL, password=EMT_PASSWORD)

    try:
        token = client.login()
        if not token:
            print("No se pudo obtener el accessToken. Revisa las credenciales.")
            return 1
    except EMTApiError as exc:
        print(f"Error de autenticación: {exc}")
        return 1

    print(f"\nLínea {line_id} — dirección {direction}\n")

    try:
        data = client.line_stops(line_id, direction)
    except EMTApiError as exc:
        print(f"Error consultando paradas: {exc}")
        return 1

    paradas: List[Dict[str, Any]] = []
    if data and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
        paradas = data["data"][0].get("stops", []) or []

    if not paradas:
        print("No se encontraron paradas.")
        return 0

    print(f"{'CÓDIGO':<8} | {'NOMBRE':<40} | {'DIRECCIÓN'}")
    print("-" * 70)
    for p in paradas:
        print(_formatear_parada(p))
    print(f"\nTotal: {len(paradas)} paradas\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
