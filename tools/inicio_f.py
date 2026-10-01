"""La F en la portada (index.html), que es la vista de las capturas del usuario.

El visor del inicio va solo: recorre el alfabeto y escribe la letra debajo. Su
controlador vive dentro de una funcion anonima, asi que no se le puede pedir la
letra; lo que se hace es esperar a que el rotulo diga F y fotografiar el escenario
del avatar en ese momento. Camara a 1.55 m, la del HTML, sin tocar nada.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

VISOR_CACHE = Path(__file__).resolve().parent / "cache" / "model-viewer.min.js"
OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "inicio_f"
URL = "http://127.0.0.1:8006/index.html"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        if VISOR_CACHE.exists():
            page.route(
                "**/@google/model-viewer*/**",
                lambda ruta: ruta.fulfill(
                    path=str(VISOR_CACHE), content_type="application/javascript"
                ),
            )
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("#hero-avatar-letter", timeout=30000)

        # el rotulo cambia al arrancar la transicion y cada letra dura poco mas de
        # 2.8 s (2 s de transicion + la pausa), asi que hay que cazar el momento:
        # se espera a que aparezca la F y se cuentan los 2 s de la transicion
        letra = None
        for _ in range(1200):
            letra = page.inner_text("#hero-avatar-letter").strip()
            if letra == "F":
                break
            time.sleep(0.1)
        if letra != "F":
            browser.close()
            raise SystemExit(f"el visor del inicio no llego a la F (iba por {letra!r})")

        time.sleep(2.0)
        destino = OUT / "F_inicio.png"
        # la portada tiene animaciones de CSS y el recorte por elemento no llega a
        # estar "quieto" nunca; se fotografia la pagina y se corta por su caja
        caja = page.query_selector(".hero-avatar-stage").bounding_box()
        page.screenshot(path=str(destino), clip=caja)
        print("rotulo:", page.inner_text("#hero-avatar-letter").strip())
        print("captura:", destino)
        browser.close()


if __name__ == "__main__":
    main()
