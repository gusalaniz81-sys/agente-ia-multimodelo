

import requests

from modulos.investigacion_web.extraer_producto import extraer_producto


def investigar_producto(url):
    # Por ahora permitimos solamente nuestra página de prueba.
    if url != "https://example.com":
        return {"error": "Sitio no habilitado para esta prueba."}

    try:
        respuesta = requests.get(
            url,
            timeout=10,
            allow_redirects=False
        )

        respuesta.raise_for_status()

        if respuesta.is_redirect:
            return {"error": "No se permiten redirecciones."}

        if "text/html" not in respuesta.headers.get("Content-Type", ""):
            return {"error": "La respuesta no contiene HTML."}

        html = respuesta.content[:200_000]

        producto = extraer_producto(html)

        return {
            "url": url,
            "resultado": producto
        }

    except requests.RequestException as error:
        return {"error": f"Error de consulta: {error}"}
