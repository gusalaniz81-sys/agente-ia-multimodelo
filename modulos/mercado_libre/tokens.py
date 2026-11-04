#cat > modulos/mercado_libre/tokens.py << 'EOF'
import json
import os
import re
import secrets
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROYECTO = Path(__file__).resolve().parents[2]
load_dotenv(PROYECTO / ".env")

DATOS = PROYECTO / "datos"
URL_TOKEN = "https://api.mercadolibre.com/oauth/token"
MARGEN = 300  # renovar 5 minutos antes de que venza


def cuentas_conectadas():
    ids = []
    for archivo in sorted(DATOS.glob("ml_tokens_*.json")):
        user_id = archivo.stem.removeprefix("ml_tokens_")
        if re.fullmatch(r"\d+", user_id):
            ids.append(user_id)
    return ids


def _guardar(user_id, tokens):
    archivo = DATOS / f"ml_tokens_{user_id}.json"
    temporal = DATOS / f".ml_tokens_{user_id}_{secrets.token_hex(8)}.tmp"

    try:
        descriptor = os.open(
            temporal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as f:
            json.dump(tokens, f)
        os.replace(temporal, archivo)
    finally:
        temporal.unlink(missing_ok=True)


def _renovar(user_id, actuales):
    app_id = os.getenv("ML_APP_ID")
    secret = os.getenv("ML_CLIENT_SECRET")

    if not app_id or not secret:
        return {"error": "Falta configurar Mercado Libre en .env"}

    try:
        respuesta = requests.post(
            URL_TOKEN,
            data={
                "grant_type": "refresh_token",
                "client_id": app_id,
                "client_secret": secret,
                "refresh_token": actuales["refresh_token"],
            },
            timeout=15,
        )

        if not respuesta.ok:
            return {
                "error": (
                    f"No se pudo renovar el acceso (HTTP {respuesta.status_code}). "
                    "Puede ser necesario volver a autorizar la cuenta."
                )
            }

        nuevo = respuesta.json()

        if not nuevo.get("access_token"):
            return {"error": "La renovacion no devolvio un token valido."}

        tokens = {
            "user_id": user_id,
            "access_token": nuevo["access_token"],
            # El refresh token se usa una sola vez: hay que guardar el nuevo.
            "refresh_token": nuevo.get("refresh_token") or actuales["refresh_token"],
            "expires_in": nuevo.get("expires_in"),
            "obtenido_en": int(time.time()),
        }

        _guardar(user_id, tokens)
        return {"token": tokens["access_token"], "user_id": user_id}

    except (OSError, ValueError, KeyError, TypeError,
            requests.RequestException) as error:
        return {"error": f"No se pudo renovar el acceso: {type(error).__name__}"}


def obtener_token(user_id=None):
    cuentas = cuentas_conectadas()

    if not cuentas:
        return {"error": "No hay cuentas conectadas."}

    if user_id is None:
        if len(cuentas) > 1:
            return {"error": "Hay varias cuentas conectadas: indica cual usar."}
        user_id = cuentas[0]

    user_id = str(user_id)

    if user_id not in cuentas:
        return {"error": "Esa cuenta no esta conectada."}

    try:
        archivo = DATOS / f"ml_tokens_{user_id}.json"
        tokens = json.loads(archivo.read_text(encoding="utf-8"))
        vence = tokens["obtenido_en"] + int(tokens["expires_in"])
    except (OSError, ValueError, KeyError, TypeError):
        return {"error": "El archivo de tokens no es valido. Autoriza de nuevo."}

    if time.time() < vence - MARGEN:
        return {"token": tokens["access_token"], "user_id": user_id}

    return _renovar(user_id, tokens)
EOF