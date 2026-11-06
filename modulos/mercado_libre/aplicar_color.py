import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from modulos.mercado_libre.tokens import obtener_token

PROYECTO = Path(__file__).resolve().parent.parent.parent
BASE = PROYECTO / "datos" / "publicaciones_ml.db"
API = "https://api.mercadolibre.com"

CAMBIOS = {
    "MLA2029766098": {
        "color": "NEGRO",
        "titulo": "Kit Entrenamiento Casa Colchoneta Negra Rusa 3kg Mancuernas",
    },
    "MLA2029934410": {
        "color": "ROSA",
        "titulo": "Kit Entrenamiento Casa Colchoneta Rosa Rusa 3kg Mancuernas",
    },
    "MLA1549218595": {
        "color": "NEGRO",
        "titulo": "Kit Entrenamiento 3 Casa Colchoneta Negra Rusa Mancuernas",
    },
}

BLOQUE = """COLOR DEL KIT
La colchoneta de este kit es de color {color}.
Los demás elementos pueden venir en otros colores (negro, azul, rojo, rosa, violeta u otros), según la disponibilidad al preparar tu pedido, y no necesariamente combinan entre sí.
Las fotos muestran ejemplos de posibles combinaciones.

Lo que no cambia es el contenido del kit: siempre se respetan los productos, las cantidades, las medidas y los pesos indicados."""

SECCION = re.compile(
    r"COMBINACIONES DE COLORES.*?Lo que no cambia[^\n]*(?:\n(?!\s*\n)[^\n]*)*",
    re.DOTALL | re.IGNORECASE,
)


def nueva_descripcion(actual, color):
    if "COLOR DEL KIT" in actual:
        return None, "ya tiene la sección nueva"

    bloque = BLOQUE.format(color=color)
    if SECCION.search(actual):
        return SECCION.sub(lambda _: bloque, actual, count=1), "reemplaza la sección de colores"
    base = re.sub(r"^Vienen en color[^\n]*\n?", "", actual, flags=re.MULTILINE | re.IGNORECASE).rstrip()
    return f"{base}\n\n{bloque}", "agrega la sección al final"


def mensaje(respuesta):
    try:
        datos = respuesta.json()
    except ValueError:
        return f"HTTP {respuesta.status_code}"
    if not isinstance(datos, dict):
        return f"HTTP {respuesta.status_code} | {str(datos)[:300]}"
    causa = datos.get("cause")
    causas = "; ".join(
        str(c.get("message")) for c in causa if isinstance(c, dict)
    ) if isinstance(causa, list) else ""
    return f"HTTP {respuesta.status_code} | {str(causas or datos.get('message') or datos.get('error') or datos)[:300]}"


def main():
    aplicar = "--aplicar" in sys.argv
    acceso = obtener_token()
    if "token" not in acceso:
        raise SystemExit(f"Sin token: {acceso.get('error', 'respuesta inesperada')}")

    cabeceras = {"Authorization": f"Bearer {acceso['token']}"}
    print("MODO: APLICAR CAMBIOS" if aplicar else "MODO: VISTA PREVIA (no cambia nada)")

    with sqlite3.connect(BASE) as conexion:
        conexion.execute(
            "CREATE TABLE IF NOT EXISTS respaldos "
            "(id TEXT, titulo TEXT, descripcion TEXT, fecha TEXT)"
        )

        for item_id, cambio in CAMBIOS.items():
            item = requests.get(
                f"{API}/items/{item_id}",
                headers=cabeceras,
                params={"attributes": "title,status"},
                timeout=20,
            )
            detalle = requests.get(f"{API}/items/{item_id}/description", headers=cabeceras, timeout=20)
            print(f"\n=== {item_id}")

            if item.status_code != 200 or detalle.status_code != 200:
                print("No se pudo leer la publicación. No se cambia nada.")
                print("  Publicación:", mensaje(item))
                print("  Descripción:", mensaje(detalle))
                continue

            titulo = item.json().get("title")
            actual = detalle.json().get("plain_text") or ""
            if not actual.strip():
                print("La descripción está vacía o no se pudo leer. No se cambia nada.")
                continue

            texto, accion = nueva_descripcion(actual, cambio["color"])
            print(f"Estado: {item.json().get('status')}")
            print(f"Título actual: {titulo}")
            print(f"Título nuevo:  {cambio['titulo']} ({len(cambio['titulo'])} caracteres)")
            print(f"Descripción: {accion}")
            if texto:
                print(f"--- Descripción nueva ---\n{texto}\n--- Fin ---")

            if not aplicar:
                continue

            conexion.execute(
                "INSERT INTO respaldos VALUES (?, ?, ?, ?)",
                (item_id, titulo, actual, datetime.now(timezone.utc).isoformat()),
            )
            conexion.commit()

            if texto:
                r = requests.put(
                    f"{API}/items/{item_id}/description",
                    headers=cabeceras,
                    params={"api_version": 2},
                    json={"plain_text": texto},
                    timeout=20,
                )
                print("Descripción:", "actualizada" if r.status_code == 200 else f"ERROR {mensaje(r)}")

            r = requests.put(
                f"{API}/items/{item_id}",
                headers=cabeceras,
                json={"title": cambio["titulo"]},
                timeout=20,
            )
            print("Título:", "actualizado" if r.status_code == 200 else f"ERROR {mensaje(r)}")


if __name__ == "__main__":
    main()