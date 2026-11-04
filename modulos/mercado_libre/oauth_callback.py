
import json
import os
import re
import secrets
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs

import requests
from dotenv import load_dotenv

PROYECTO = Path(__file__).resolve().parents[2]
load_dotenv(PROYECTO / ".env")

PENDIENTE = PROYECTO / "datos" / "oauth_pendiente.json"


class ReceptorOAuth(BaseHTTPRequestHandler):

    def responder(self, estado, mensaje):
        contenido = mensaje.encode("utf-8")

        self.send_response(estado)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(contenido)

    def do_GET(self):
        solicitud = urlsplit(self.path)

        if solicitud.path == "/":
            self.responder(200, "Servidor OAuth local funcionando.")
            return

        if solicitud.path != "/callback":
            self.responder(404, "Ruta no encontrada.")
            return

        try:
            parametros = parse_qs(
                solicitud.query,
                max_num_fields=10
            )

            estados = parametros.get("state", [])
            codigos = parametros.get("code", [])

            if len(estados) != 1 or len(codigos) != 1:
                self.responder(403, "Autorizacion no valida.")
                return

            if not PENDIENTE.is_file():
                self.responder(403, "No existe una autorizacion pendiente.")
                return

            pendiente = json.loads(
                PENDIENTE.read_text(encoding="utf-8")
            )

            if time.time() > pendiente["expira"]:
                self.responder(403, "Autorizacion vencida.")
                return

            if not secrets.compare_digest(
                estados[0], pendiente["state"]
            ):
                self.responder(403, "Estado de seguridad incorrecto.")
                return

            app_id = os.getenv("ML_APP_ID")
            secret = os.getenv("ML_CLIENT_SECRET")
            redirect = os.getenv("ML_REDIRECT_URI")

            if not all((app_id, secret, redirect)):
                self.responder(500, "Configuracion incompleta.")
                return

            # El intento se consume para evitar reutilizarlo.
            PENDIENTE.unlink()

            respuesta = requests.post(
                "https://api.mercadolibre.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": app_id,
                    "client_secret": secret,
                    "code": codigos[0],
                    "redirect_uri": redirect,
                    "code_verifier": pendiente["code_verifier"]
                },
                timeout=15
            )

            if not respuesta.ok:
                print("Error OAuth HTTP:", respuesta.status_code)
                self.responder(502, "No se pudo completar la autorizacion.")
                return

            datos = respuesta.json()
            usuario = str(datos.get("user_id", ""))

            if not re.fullmatch(r"\d+", usuario):
                self.responder(502, "Respuesta OAuth no valida.")
                return

            if not datos.get("access_token") or not datos.get("refresh_token"):
                self.responder(502, "Faltan tokens en la respuesta.")
                return

            archivo = PROYECTO / "datos" / f"ml_tokens_{usuario}.json"
            temporal = PROYECTO / "datos" / (
                f".ml_tokens_{usuario}_{secrets.token_hex(8)}.tmp"
            )

            try:
                descriptor = os.open(
                    temporal,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600
                )

                with os.fdopen(descriptor, "w", encoding="utf-8") as f:
                    json.dump({
                        "user_id": usuario,
                        "access_token": datos["access_token"],
                        "refresh_token": datos["refresh_token"],
                        "expires_in": datos.get("expires_in"),
                        "obtenido_en": int(time.time())
                    }, f)

                os.replace(temporal, archivo)

            finally:
                temporal.unlink(missing_ok=True)

            print("Cuenta autorizada correctamente.")
            self.responder(200, "Cuenta conectada correctamente.")

        except (OSError, ValueError, KeyError,
                TypeError, requests.RequestException) as error:
            print("Error en OAuth:", type(error).__name__)
            self.responder(500, "No se pudo completar la operacion.")

    def log_message(self, formato, *argumentos):
        # Evitar registrar codigos de autorizacion.
        pass


if __name__ == "__main__":
    servidor = HTTPServer(("127.0.0.1", 8765), ReceptorOAuth)
    print("Servidor OAuth escuchando en el puerto 8765")
    servidor.serve_forever()
