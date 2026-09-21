"""Que valen las medidas de la T en las letras que ya estan dadas por buenas.

Sin esto los umbrales son inventados. La A, la E y la S son el mismo puno y ya
pasaron revision, asi que sirven de calibracion: dicen cuanto vale de verdad
"el pulgar no atraviesa el indice" (gapIdxPunta) o "el pulgar va apoyado en el
frente" (sobreFrente) en este modelo, y hasta donde se puede pedir.

Tambien imprime la T de hoy, que es la que hay que sustituir.
"""
import json
from pathlib import Path

import time
from playwright.sync_api import sync_playwright

from pose_lab_e import free_camera
from pose_lab_t import MEASURE_JS
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t7"

LETRAS = ("A", "E", "S", "T", "M", "N")
CAMPOS = ("camDesvio", "camCima", "sobreFrente", "gapIdxPunta", "gapMedPunta",
          "gapBase", "gapIdx", "gapMed", "thUpDir", "thLatDir", "dobla",
          "punoMax", "huecoIM", "camDelante")


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)
        page.evaluate(
            """(a) => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = a.t;
                mv.cameraOrbit = a.orbit;
                mv.fieldOfView = a.fov;
                mv.jumpCameraToGoal();
            }""",
            {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
        )
        time.sleep(0.3)

        print(f"{'':10s}" + "".join(f"{c[:11]:>13s}" for c in CAMPOS))
        for letra in LETRAS:
            sena = por_letra.get(letra)
            if not sena or not sena.get("pose"):
                continue
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", sena["pose"]
            )
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(f"{letra:10s}" + "".join(f"{m[c]:13.3f}" for c in CAMPOS))

        browser.close()


if __name__ == "__main__":
    main()
