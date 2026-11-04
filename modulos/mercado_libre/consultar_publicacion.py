
import re

import requests

from modulos.mercado_libre.tokens import obtener_token


def consultar_publicacion(item_id):
    item_id = item_id.strip().upper()

    if not re.fullmatch(r"MLA\d{6,15}", item_id):
        return {"error": "ID de publicación inválido."}

    acceso = obtener_token()

    if "token" not in acceso:
        return {
            "error": acceso.get(
                "error",
                "Falta configurar el acceso autorizado a Mercado Libre."
            )
        }

    url = f"https://api.mercadolibre.com/items/{item_id}"

    try:
        respuesta = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {acceso['token']}",
                "Accept": "application/json"
            },
            timeout=15
        )

        if respuesta.status_code in (401, 403):
            return {"error": "Acceso no autorizado o permiso insuficiente."}

        respuesta.raise_for_status()
        datos = respuesta.json()

        envio = datos.get("shipping") or {}

        return {
            "id": datos.get("id"),
            "titulo": datos.get("title"),
            "precio": datos.get("price"),
            "moneda": datos.get("currency_id"),
            "enlace": datos.get("permalink"),
            "envio_gratis": envio.get("free_shipping")
        }

    except (requests.RequestException, ValueError) as error:
        return {
            "error": f"No se pudo completar la consulta: {type(error).__name__}"
        }