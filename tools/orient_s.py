"""S lab 3: que lado de la mano ve la camara de produccion.

De esto depende todo lo demas. Si el espectador ve el DORSO, un pulgar cruzado
por delante de los dedos queda escondido detras del puno y la S se ve igual que
la A; si ve la PALMA, el cruce se lee. Antes de fijar la pose hay que saberlo,
y no se puede deducir del render porque un puno es casi simetrico.

Se mide con la letra B, que tiene los dedos extendidos y el pulgar pegado: ahi
si se distingue a ojo, y de paso se contrasta con el signo que da la normal.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, ORIENT_JS, cam
from pose_lab_e import free_camera
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "orient_s"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s3"


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        for letra in ("B", "A", "S"):
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                por_letra[letra]["pose"],
            )
            time.sleep(0.35)
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            o = page.evaluate(ORIENT_JS)
            print(
                f"{letra}: normal->camara={o['nrmHaciaCam']:+.2f}  "
                f"pulgar a la derecha={o['pulgarDer']:+.2f}  "
                f"indice={o['indiceDer']:+.2f}  menique={o['meniqueDer']:+.2f}"
            )
            viewer.screenshot(path=str(OUT / f"{letra}_produccion.png"))

        browser.close()

    print("\nnormal->camara > 0 = el espectador ve el DORSO")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
