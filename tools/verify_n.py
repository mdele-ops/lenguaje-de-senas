"""Verifica la N por el camino real de la app (mostrarSena, no applyTestPose)."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera, set_cam
from pose_lab_m5 import hoja
from pulgar_e import PULGAR_JS
from pulgar_e import linea as linea_pulgar
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_n"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "N_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=N&v=nverify"


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    print("catalogo", cat["version"])

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        result = page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('N')")
        print("modo:", json.dumps(result, ensure_ascii=False)[:400])
        time.sleep(2.4)

        t = page.evaluate(PULGAR_JS)
        print(linea_pulgar("N", t, 0))
        caption = page.evaluate(
            "() => (document.getElementById('anim-info') || {}).textContent"
        )
        print("caption:", caption)

        hand = page.evaluate(HAND_POS_JS)
        frente, prod = [], []
        if REF.exists():
            frente.append(("REF foto", REF))
            prod.append(("REF foto", REF))

        set_cam(page, "mano", hand)
        p_f = OUT / "N_frente.png"
        viewer.screenshot(path=str(p_f))
        frente.append(("mostrarSena N", p_f))

        set_cam(page, "lado", hand)
        viewer.screenshot(path=str(OUT / "N_lado.png"))

        set_cam(page, "prod", hand)
        p_p = OUT / "N_prod.png"
        viewer.screenshot(path=str(p_p))
        prod.append(("mostrarSena N", p_p))

        browser.close()

    hoja(frente, OUT / "_frente.png", cols=2, cell=340)
    hoja(prod, OUT / "_prod.png", cols=2, cell=340)


if __name__ == "__main__":
    main()
