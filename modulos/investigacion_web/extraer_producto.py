
import json
from bs4 import BeautifulSoup


def extraer_producto(html):
    sopa = BeautifulSoup(html, "html.parser")

    scripts = sopa.find_all(
        "script",
        type="application/ld+json"
    )

    for script in scripts:
        try:
            datos = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        pendientes = [datos]

        while pendientes:
            elemento = pendientes.pop()

            if isinstance(elemento, list):
                pendientes.extend(elemento)
                continue

            if not isinstance(elemento, dict):
                continue

            tipo = elemento.get("@type", "")
            tipos = tipo if isinstance(tipo, list) else [tipo]

            if "Product" in tipos:
                oferta = elemento.get("offers", {})

                if isinstance(oferta, list):
                    oferta = oferta[0] if oferta else {}

                if not isinstance(oferta, dict):
                    oferta = {}

                return {
                    "nombre": elemento.get("name"),
                    "descripcion": elemento.get("description"),
                    "precio": oferta.get("price"),
                    "moneda": oferta.get("priceCurrency")
                }

            for clave in ("@graph", "mainEntity"):
                if clave in elemento:
                    pendientes.append(elemento[clave])

    return {"error": "No se encontraron datos estructurados de producto."}
