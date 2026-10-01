"""Regresion: comprueba que el catalogo sigue completo y que las letras vecinas
a la O (y algunas de referencia) se siguen aplicando sin error tras la edicion.
"""
import time

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("verify_vecinas")
LETRAS = ["C", "E", "N", "Ñ", "O", "P", "S"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        total = page.evaluate(
            "() => window.__LSM_CONTROLLER__.getCatalog().senas.length"
        )
        print("señas en el catalogo:", total)

        for letra in LETRAS:
            r = page.evaluate("(l) => window.__LSM_CONTROLLER__.mostrarSena(l)", letra)
            time.sleep(2.4)
            m = L.measure(page)
            print(
                f"{letra:2s} modo={r['modo']:9s} dI={m['dI']:.2f} "
                f"reach={m['reach']:.2f}"
            )
            L.set_camera(page, orbit="0deg 82deg 0.34m", fov="22deg")
            safe = "enie" if letra == "Ñ" else letra
            viewer.screenshot(path=str(OUT / f"{safe}.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
