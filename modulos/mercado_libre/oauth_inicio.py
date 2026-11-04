
import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path

from dotenv import load_dotenv

PROYECTO = Path(__file__).resolve().parents[2]
load_dotenv(PROYECTO / ".env")


def preparar_oauth():
    app_id = os.getenv("ML_APP_ID")
    redirect_uri = os.getenv("ML_REDIRECT_URI")

    if not app_id or not redirect_uri:
        print("Falta configurar Mercado Libre en .env")
        return

    # Identificador aleatorio contra solicitudes falsas
    state = secrets.token_urlsafe(32)

    # Clave temporal utilizada por PKCE
    code_verifier = secrets.token_urlsafe(48)

    # Generamos el desafío PKCE utilizando SHA-256
    resumen = hashlib.sha256(
        code_verifier.encode("ascii")
    ).digest()

    code_challenge = base64.urlsafe_b64encode(
        resumen
    ).rstrip(b"=").decode("ascii")

    datos = {
        "state": state,
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "expira": time.time() + 600
    }

    archivo = PROYECTO / "datos" / "oauth_pendiente.json"
    archivo.parent.mkdir(parents=True, exist_ok=True)

    descriptor = os.open(
        archivo,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600
    )

    os.chmod(archivo, 0o600)

    with os.fdopen(descriptor, "w", encoding="utf-8") as f:
        json.dump(datos, f)

    print("Preparación OAuth completada.")
    print("State generado correctamente.")
    print("PKCE generado correctamente.")
    print("Todavía no se autorizó ninguna cuenta.")


if __name__ == "__main__":
    preparar_oauth()
