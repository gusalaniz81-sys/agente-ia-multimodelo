
import requests
from bs4 import BeautifulSoup


def consultar_pagina(url):
    if url != "https://example.com":
        return {"error": "Página no habilitada para esta prueba."}

    try:
        respuesta = requests.get(
            url,
            timeout=10,
            allow_redirects=False
        )

        respuesta.raise_for_status()

        if respuesta.is_redirect:
            return {"error": "La página redirige a otra dirección."}

        if "text/html" not in respuesta.headers.get("Content-Type", ""):
            return {"error": "El contenido no es HTML."}

        sopa = BeautifulSoup(respuesta.content[:200_000], "html.parser")

        titulo = sopa.title.get_text(strip=True) if sopa.title else "Sin título"

        descripcion = sopa.find("meta", attrs={"name": "description"})

        return {
            "url": url,
            "titulo": titulo,
            "descripcion": descripcion.get("content", "") if descripcion else "Sin descripción"
        }

    except requests.RequestException as error:
        return {"error": f"No se pudo consultar la página: {error}"}
