
import requests

from modulos.mercado_libre.tokens import obtener_token

URL_API = "https://api.mercadolibre.com"
ESTADOS = {"active", "paused", "closed"}


def listar_publicaciones(estado=None, limite=10, desde=0):
    if estado is not None and estado not in ESTADOS:
        return {"error": "Estado inválido. Usá active, paused o closed."}

    limite = max(1, min(limite or 10, 20))
    desde = max(0, desde or 0)
    acceso = obtener_token()

    if "token" not in acceso:
        return {
            "error": acceso.get(
                "error",
                "Falta configurar el acceso autorizado a Mercado Libre."
            )
        }

    cabeceras = {
        "Authorization": f"Bearer {acceso['token']}",
        "Accept": "application/json"
    }
    parametros = {"limit": limite, "offset": desde}

    if estado:
        parametros["status"] = estado

    try:
        busqueda = requests.get(
            f"{URL_API}/users/{acceso['user_id']}/items/search",
            headers=cabeceras,
            params=parametros,
            timeout=15
        )

        if busqueda.status_code in (401, 403):
            return {"error": "Acceso no autorizado o permiso insuficiente."}

        busqueda.raise_for_status()
        datos = busqueda.json()
        ids = datos.get("results") or []
        total = (datos.get("paging") or {}).get("total", len(ids))

        if not ids:
            return {"total": total, "desde": desde, "publicaciones": []}

        detalle = requests.get(
            f"{URL_API}/items",
            headers=cabeceras,
            params={
                "ids": ",".join(ids),
                "attributes": "id,title,price,currency_id,status"
            },
            timeout=15
        )

        if detalle.status_code in (401, 403):
            return {"error": "Acceso no autorizado o permiso insuficiente."}

        detalle.raise_for_status()
        publicaciones = []

        for elemento in detalle.json():
            if elemento.get("code") != 200:
                continue

            cuerpo = elemento.get("body") or {}
            publicaciones.append({
                "id": cuerpo.get("id"),
                "titulo": cuerpo.get("title"),
                "precio": cuerpo.get("price"),
                "moneda": cuerpo.get("currency_id"),
                "estado": cuerpo.get("status")
            })

        return {"total": total, "desde": desde, "publicaciones": publicaciones}

    except (requests.RequestException, ValueError) as error:
        return {
            "error": f"No se pudo completar la consulta: {type(error).__name__}"
        }
