"""Servidor estatico para las pruebas, multihilo.

`python -m http.server` atiende de uno en uno: mientras manda los 48 MB de
model.glb deja en cola el resto de la pagina, y el visor se queda colgado en
"Descargando visor 3D". Con ThreadingHTTPServer eso no pasa.
"""
import shutil
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "0.0.0.0"
PUERTO = 8006


class Silencioso(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".glb": "model/gltf-binary",
        ".gltf": "model/gltf+json",
        ".wasm": "application/wasm",
        ".css": "text/css",
        ".json": "application/json",
    }
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if "model.glb" in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile, length=256 * 1024)


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO
    handler = partial(Silencioso, directory=str(ROOT))
    with ThreadingHTTPServer((HOST, puerto), handler) as httpd:
        print(f"sirviendo {ROOT}", flush=True)
        print(f"  local:   http://127.0.0.1:{puerto}", flush=True)
        print(f"  red:     http://10.4.145.88:{puerto}", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
