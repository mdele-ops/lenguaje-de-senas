"""La O tal como la abre practica.html?letra=O, sin poses de prueba."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9 as se9

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "o_redonda"
se9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=opagina"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = se9.abrir(p)
        page.set_viewport_size({"width": 1280, "height": 900})
        time.sleep(1)
        page.query_selector("#handViewer").screenshot(path=str(OUT / "pagina_O_antes.png"))
        print(page.evaluate(
            "() => window.__LSM_CONTROLLER__.mostrarSena('O', { loop: false }).modo"
        ))
        time.sleep(3)
        print(page.evaluate(
            "() => { const s = window.__LSM_CONTROLLER__.getSena('O');"
            " return { curl: s.pose.index.curl, medio: s.pose.middle.curl, muneca: s.pose.muneca }; }"
        ))
        page.query_selector("#handViewer").screenshot(path=str(OUT / "pagina_O.png"))
        browser.close()


if __name__ == "__main__":
    main()
