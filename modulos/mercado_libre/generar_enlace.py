import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv

PROYECTO = Path(__file__).resolve().parents[2]
load_dotenv(PROYECTO / ".env")

PENDIENTE = PROYECTO / "datos" / "oauth_pendiente.json"
URL_AUTORIZACION = "https://auth.mercadolibre.com.ar/authorization"


def generar_enlace():
    app_id = os.getenv("ML_APP_ID")
    redirect_uri = os.getenv("ML_REDIRECT_URI")

    if not app_id or not redirect_uri:
        print("Falta configurar Mercado Libre en .env")
        return None

    if not PENDIENTE.is_file():
        print("No hay preparacion pendiente. Ejecuta primero oauth_inicio.py")
        return None

    try:
        pendiente = json.loads(PENDIENTE.read_text(encoding="utf-8"))
        state = pendiente["state"]
        challenge = pendiente["code_challenge"]
        expira = pendiente["expira"]
    except (OSError, ValueError, KeyError):
        print("La preparacion no es valida. Ejecuta oauth_inicio.py de nuevo.")
        return None

    if time.time() > expira:
        print("La preparacion vencio. Ejecuta oauth_inicio.py de nuevo.")
        return None

    parametros = {
        "response_type": "code",
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    return f"{URL_AUTORIZACION}?{urlencode(parametros)}"


if __name__ == "__main__":
    enlace = generar_enlace()
    if enlace:
        print("Abri este enlace en el navegador antes de que pasen 10 minutos:")
        print(enlace)
