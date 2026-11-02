
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit


class ReceptorOAuth(BaseHTTPRequestHandler):

    def do_GET(self):
        ruta = urlsplit(self.path).path

        if ruta == "/":
            mensaje = "Servidor OAuth local funcionando."
            estado = 200

        elif ruta == "/callback":
            mensaje = "Autorizacion OAuth todavia no habilitada."
            estado = 403

        else:
            mensaje = "Ruta no encontrada."
            estado = 404

        contenido = mensaje.encode("utf-8")

        self.send_response(estado)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def log_message(self, formato, *argumentos):
        # Evitamos registrar URLs con posibles codigos OAuth.
        pass


if __name__ == "__main__":
    servidor = HTTPServer(("127.0.0.1", 8765), ReceptorOAuth)
    print("Servidor OAuth escuchando en el puerto 8765")
    servidor.serve_forever()
