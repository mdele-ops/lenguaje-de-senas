"""Eleccion final de la E: cuanto se cierran los dedos, con el pulgar ya fijado.

El pulgar ganador de refine_e14 es el "corto95": recogido del lado del indice,
punta a media palma bajo la yema del indice y sin sobresalir (tLen 0.36).
Aqui solo queda decidir el cierre de los cuatro dedos y la separacion.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from pose_lab_e import free_camera
from refine_e14 import score_pulgar
from search_e11 import MEASURE_JS
from search_e13 import pose_e, score_dedos
from search_e14 import linea
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "final_e14"
REF = ROOT / "tools" / "screenshots" / "referencia"

PULGAR = (0.95, -0.6, -50, 0, -30, 0, 75)

CASOS = {
    "1_curl84_sep4": (0.84, -4),
    "2_curl88_sep4": (0.88, -4),
    "3_curl92_sep4": (0.92, -4),
    "4_curl96_sep4": (0.96, -4),
    "5_curl92_sep8": (0.92, -8),
    "6_curl92_sep0": (0.92, 0),
}

VISTAS = {
    "app": ("0deg 84deg 1.15m", "14deg"),
    "cerca": ("0deg 84deg 0.55m", "12deg"),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    senas = {s["letra"]: s for s in cat["senas"]}

    casos = {"0_E_actual": senas["E"]["pose"]}
    for nombre, (curl, conv) in CASOS.items():
        casos[nombre] = pose_e(curl, conv, *PULGAR)

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.6)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        salida = {v: [] for v in VISTAS}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.45)
            m = page.evaluate(MEASURE_JS)
            print(linea(nombre, m, score_dedos(m) + score_pulgar(m)))

            hand = page.evaluate(HAND_TARGET_JS)
            t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
            for vista, (orbit, fov) in VISTAS.items():
                for _ in range(2):
                    page.evaluate(
                        """(a) => {
                            const mv = document.getElementById('handViewer');
                            mv.cameraTarget = a.t;
                            mv.cameraOrbit = a.o;
                            mv.fieldOfView = a.f;
                            mv.jumpCameraToGoal();
                        }""",
                        {"t": t, "o": orbit, "f": fov},
                    )
                    time.sleep(0.3)
                salida[vista].append(
                    (nombre, recorte(page, viewer, OUT / f"{nombre}_{vista}.png", False))
                )
        browser.close()

    ref = [(n, p) for n, p in [("REF foto", REF / "E_usuario.png")] if p.exists()]
    for vista, imgs in salida.items():
        hoja(ref + imgs, OUT / f"_{vista}.png", cols=4, cell=300)


if __name__ == "__main__":
    main()
