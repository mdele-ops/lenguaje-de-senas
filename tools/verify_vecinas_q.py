"""Regresion alrededor de la Q: que no se confunda con sus vecinas de forma.

La Q comparte esqueleto con la G (indice y pulgar extendidos) y con la D y la
O (pulgar buscando al indice). Se aplican todas desde el catalogo real, se
comprueba que ninguna da error y se deja una hoja para mirarlas juntas.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_p7 import hoja
from pose_lab_q import MEASURE_JS
from pose_lab_q2 import apertura, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_vecinas_q"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vecq"

LETRAS = ["D", "G", "O", "P", "Q"]


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        total = page.evaluate(
            "() => window.__LSM_CONTROLLER__.getCatalog().senas.length"
        )
        print("señas en el catalogo:", total)

        items = []
        for letra in LETRAS:
            r = page.evaluate("(l) => window.__LSM_CONTROLLER__.mostrarSena(l)", letra)
            time.sleep(2.5)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{letra:2s} modo={r['modo']:8s} idx={m['idxAng']:+7.1f} "
                f"th={m['thAng']:+7.1f} pico={apertura(m):5.1f} "
                f"sep={m['pico']:.2f} puno={m['punoMax']:.2f}"
            )
            mano = page.evaluate(HAND_POS_JS)
            # en la Q los dedos cuelgan por debajo de la muñeca: sin bajar el
            # encuadre el pico se sale del recorte
            cam(
                page,
                "%.3fm %.3fm %.3fm" % (mano["x"], mano["y"] - 0.03, mano["z"]),
                "0deg 84deg 1.10m",
                "21deg",
            )
            path = OUT / f"{letra}.png"
            viewer.screenshot(path=str(path))
            items.append((letra, path))

        browser.close()

    hoja(items, OUT / "_vecinas.png", cols=5, cell=320)


if __name__ == "__main__":
    main()
