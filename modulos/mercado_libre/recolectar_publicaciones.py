import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from modulos.mercado_libre.tokens import obtener_token

PROYECTO = Path(__file__).resolve().parent.parent.parent
BASE = PROYECTO / "datos" / "publicaciones_ml.db"
API = "https://api.mercadolibre.com"
PALABRAS = (
    "kit entrenamiento", "gimnasio", "fitness", "mancuerna", "colchoneta",
    "tobillera", "pesa", "banda elastica", "banda elástica", "soga", "yoga"
)
CONSULTAS = (
    "kit entrenamiento pesa rusa mancuernas colchoneta",
    "kit gimnasio en casa pesas colchoneta",
    "kit fitness mancuernas tobilleras colchoneta",
    "kit entrenamiento funcional en casa",
)
CAMPOS = (
    "id,title,price,currency_id,status,listing_type_id,category_id,"
    "pictures,attributes,shipping,sold_quantity"
)


def crear_pedido(cabeceras):
    def pedir(ruta, **parametros):
        for intento in range(3):
            try:
                respuesta = requests.get(
                    f"{API}{ruta}", headers=cabeceras, params=parametros, timeout=20
                )
            except requests.RequestException:
                return None, None

            if respuesta.status_code == 429:
                time.sleep(5 * (intento + 1))
                continue
            if respuesta.status_code != 200:
                return respuesta.status_code, None
            try:
                return 200, respuesta.json()
            except ValueError:
                return 200, None
        return 429, None

    return pedir


def resumir_atributos(atributos):
    return json.dumps(
        [
            {"nombre": a.get("name"), "valor": a.get("value_name")}
            for a in atributos or []
            if a.get("value_name")
        ],
        ensure_ascii=False,
    )


def preparar_base(conexion):
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS publicaciones (
            id TEXT PRIMARY KEY,
            origen TEXT NOT NULL,
            producto_id TEXT,
            vendedor_id TEXT,
            titulo TEXT,
            precio REAL,
            moneda TEXT,
            estado TEXT,
            tipo TEXT,
            categoria TEXT,
            fotos INTEGER,
            envio_gratis INTEGER,
            ventas INTEGER,
            visitas INTEGER,
            atributos TEXT,
            descripcion TEXT,
            fuente_descripcion TEXT,
            actualizado TEXT NOT NULL
        )
        """
    )


def guardar(conexion, **fila):
    columnas = ",".join(fila)
    marcas = ",".join("?" for _ in fila)
    conexion.execute(
        f"INSERT OR REPLACE INTO publicaciones ({columnas}) VALUES ({marcas})",
        tuple(fila.values()),
    )


def recolectar_propias(conexion, pedir, user_id, ahora):
    ids = set()
    desde = 0
    while True:
        estado, datos = pedir(f"/users/{user_id}/items/search", limit=50, offset=desde)
        if estado != 200 or not datos:
            raise SystemExit(f"No se pudo listar la cuenta: HTTP {estado}")
        lote = datos.get("results") or []
        ids.update(lote)
        desde += len(lote)
        if not lote or desde >= datos["paging"]["total"]:
            break

    ids = sorted(ids)
    elegidas = []
    for i in range(0, len(ids), 20):
        estado, detalle = pedir("/items", ids=",".join(ids[i:i + 20]), attributes=CAMPOS)
        if estado != 200:
            print(f"Aviso: falló un lote de publicaciones (HTTP {estado})")
            continue
        for elemento in detalle or []:
            if elemento.get("code") == 200:
                cuerpo = elemento["body"]
                titulo = str(cuerpo.get("title")).lower()
                if any(palabra in titulo for palabra in PALABRAS):
                    elegidas.append(cuerpo)

    con_descripcion = 0
    for numero, p in enumerate(elegidas, start=1):
        _, visitas = pedir("/visits/items", ids=p["id"])
        _, descripcion = pedir(f"/items/{p['id']}/description")
        texto = (descripcion or {}).get("plain_text") or None
        con_descripcion += 1 if texto else 0
        guardar(
            conexion,
            id=p["id"],
            origen="propia",
            producto_id=None,
            vendedor_id=str(user_id),
            titulo=p.get("title"),
            precio=p.get("price"),
            moneda=p.get("currency_id"),
            estado=p.get("status"),
            tipo=p.get("listing_type_id"),
            categoria=p.get("category_id"),
            fotos=len(p.get("pictures") or []),
            envio_gratis=int(bool((p.get("shipping") or {}).get("free_shipping"))),
            ventas=p.get("sold_quantity"),
            visitas=(visitas or {}).get(p["id"]),
            atributos=resumir_atributos(p.get("attributes")),
            descripcion=texto,
            fuente_descripcion="publicacion" if texto else None,
            actualizado=ahora,
        )
        if numero % 25 == 0:
            conexion.commit()
            print(f"Propias: {numero} de {len(elegidas)}")
        time.sleep(0.2)

    conexion.commit()
    return len(elegidas), con_descripcion


def texto_de_producto(producto):
    partes = [
        str(rasgo.get("text"))
        for rasgo in producto.get("main_features") or []
        if rasgo.get("text")
    ]
    corta = (producto.get("short_description") or {}).get("content")
    if corta:
        partes.append(str(corta))
    return "\n".join(partes) or None


def recolectar_competencia(conexion, pedir, user_id, ahora):
    productos = {}
    for consulta in CONSULTAS:
        estado, datos = pedir(
            "/products/search", site_id="MLA", status="active", q=consulta, limit=15
        )
        if estado != 200:
            print(f"Aviso: falló la búsqueda '{consulta}' (HTTP {estado})")
            continue
        for producto in (datos or {}).get("results") or []:
            productos[producto.get("id")] = producto.get("name")

    resumen = {"productos": len(productos), "ofertas": 0, "publicacion": 0, "catalogo": 0, "sin_texto": 0}
    for producto_id, nombre in productos.items():
        _, ofertas = pedir(f"/products/{producto_id}/items", limit=5)
        ofertas = (ofertas or {}).get("results") or []
        if not ofertas:
            continue
        _, producto = pedir(f"/products/{producto_id}")
        producto = producto or {}
        texto_catalogo = texto_de_producto(producto)

        for oferta in ofertas:
            if str(oferta.get("seller_id")) == str(user_id):
                continue
            item_id = oferta.get("item_id")
            clave = item_id or f"{producto_id}-{oferta.get('seller_id')}"
            descripcion = None
            if item_id:
                _, datos_descripcion = pedir(f"/items/{item_id}/description")
                descripcion = (datos_descripcion or {}).get("plain_text") or None

            fuente = "publicacion" if descripcion else ("catalogo" if texto_catalogo else None)
            resumen["ofertas"] += 1
            resumen[fuente or "sin_texto"] += 1

            guardar(
                conexion,
                id=clave,
                origen="competencia",
                producto_id=producto_id,
                vendedor_id=str(oferta.get("seller_id")),
                titulo=nombre,
                precio=oferta.get("price"),
                moneda=oferta.get("currency_id"),
                estado=oferta.get("status") or "active",
                tipo=oferta.get("listing_type_id"),
                categoria=oferta.get("category_id"),
                fotos=len(producto.get("pictures") or []),
                envio_gratis=int(bool((oferta.get("shipping") or {}).get("free_shipping"))),
                ventas=None,
                visitas=None,
                atributos=resumir_atributos(producto.get("attributes")),
                descripcion=descripcion or texto_catalogo,
                fuente_descripcion=fuente,
                actualizado=ahora,
            )
            time.sleep(0.2)

    conexion.commit()
    return resumen


def main():
    acceso = obtener_token()
    if "token" not in acceso:
        raise SystemExit(f"Sin token: {acceso.get('error', 'respuesta inesperada')}")

    pedir = crear_pedido({"Authorization": f"Bearer {acceso['token']}"})
    ahora = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(BASE) as conexion:
        preparar_base(conexion)
        propias, con_descripcion = recolectar_propias(conexion, pedir, acceso["user_id"], ahora)
        competencia = recolectar_competencia(conexion, pedir, acceso["user_id"], ahora)

        print(f"\nPropias: {propias} | con descripción: {con_descripcion}")
        print(f"Competencia: {competencia}")

        ejemplo = conexion.execute(
            "SELECT id, titulo, descripcion FROM publicaciones "
            "WHERE origen = 'propia' AND descripcion IS NOT NULL "
            "ORDER BY ventas DESC LIMIT 1"
        ).fetchone()
        if ejemplo:
            print(f"\nEjemplo propio: {ejemplo[0]} | {ejemplo[1]}\n{ejemplo[2][:700]}")

    print(f"\nGuardado en {BASE.relative_to(PROYECTO)}")


if __name__ == "__main__":
    main()
