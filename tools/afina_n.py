"""Afina la N: cuanto se cierran anular y menique y donde apoya el pulgar.

De lab_n3 salio la forma (indice y medio colgando, muneca x150 como la M).
Lo que queda por decidir es el puno: en la lamina el anular y el menique no
se ven, quedan recogidos con el pulgar encima, y los dos dedos que cuelgan se
distinguen uno del otro (no se fusionan en un solo bulto).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import BONES, T2, T3, free_camera
from pose_lab_m5 import hoja
from pose_lab_n3 import MEASURE_JS, pose_n
from search_e9 import abrir
from ver_n3 import CENTRO_JS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "afina_n"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "N_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=afinan"

PUNO = {
    BONES["ring"][1]: {"x": 16},
    BONES["ring"][2]: {"x": 20},
    BONES["pinky"][1]: {"x": 16},
    BONES["pinky"][2]: {"x": 20},
}
PUNO_MAS = {
    BONES["ring"][0]: {"x": 8},
    BONES["ring"][1]: {"x": 24},
    BONES["ring"][2]: {"x": 26},
    BONES["pinky"][0]: {"x": 8},
    BONES["pinky"][1]: {"x": 24},
    BONES["pinky"][2]: {"x": 26},
}

CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
CASES = {
    "01_M": next(s for s in CAT["senas"] if s["letra"] == "M")["pose"],
    "P1_puno": pose_n(spread=(6, -2), extra=PUNO),
    "P2_puno_mas": pose_n(spread=(6, -2), extra=PUNO_MAS),
    "P3_pulgar": pose_n(
        spread=(6, -2), tcurl=0.62, taside=-0.34, t2x=22, t3x=14, extra=PUNO_MAS
    ),
    "P4_convergen": pose_n(spread=(9, -3), extra=PUNO_MAS),
    "P5_x156": pose_n(spread=(6, -2), mx=156, extra=PUNO_MAS),
}

VISTAS = {"dorso": (0, 82, 1.85), "media": (-30, 82, 1.85), "lado": (-70, 82, 2.0)}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 760, "height": 760})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        hojas = {k: [("REF foto", REF)] for k in VISTAS}
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.32)
            m = page.evaluate(MEASURE_JS)
            c = page.evaluate(CENTRO_JS)
            print(
                f"{name:14s} down={m['idxDown']:+.2f}/{m['midDown']:+.2f} "
                f"tog={m['togIM']:.2f} ringUp={m['ringUp']:+.2f} "
                f"tPulgarAnular={m['thumbRing']:.2f}"
            )
            for vista, (theta, phi, k) in VISTAS.items():
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.orbit;
                        mv.fieldOfView = '26deg';
                        mv.jumpCameraToGoal();
                    }""",
                    {
                        "t": "%.3fm %.3fm %.3fm" % (c["x"], c["y"], c["z"]),
                        "orbit": f"{theta}deg {phi}deg {max(0.3, c['size'] * k):.3f}m",
                    },
                )
                time.sleep(0.15)
                ruta = OUT / f"{name}_{vista}.png"
                viewer.screenshot(path=str(ruta))
                hojas[vista].append((name, ruta))

        browser.close()

    for vista, items in hojas.items():
        hoja(items, OUT / f"_{vista}.png", cols=3, cell=330)
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
