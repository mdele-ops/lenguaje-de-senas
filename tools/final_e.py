"""Vista de eleccion de la E: plano medio (como se aprecia en la app al
acercarse) de las candidatas finalistas, con y sin huesos."""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from pose_lab_e import free_camera
from search_e10 import SCREEN_JS, linea, puntuar
from search_e9 import MEASURE_JS, abrir, pose_e

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "final_e"
REF = ROOT / "tools" / "screenshots" / "referencia"

# plano medio: lo bastante cerca para ver los dedos, lo bastante lejos para que
# la perspectiva no deforme (el primer plano a 0.62 m enganaba)
VISTAS = {
    "frente": ("0deg 84deg 1.15m", "14deg"),
    "tresquartos": ("-38deg 84deg 1.15m", "14deg"),
}


def catalogo_actual():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    return next(s for s in cat["senas"] if s["letra"] == "E")["pose"]


FINALISTAS = {
    "0_actual": catalogo_actual(),
    "A": pose_e(85, 85, 0, -4, 0.9, -0.5, -60, 15, 60, 70),
    "C": pose_e(85, 100, 20, -4, 0.9, -0.5, -60, 15, 60, 70),
    "G": pose_e(85, 85, 0, -4, 0.9, -0.5, -60, 15, 60, 85),
    "I": pose_e(85, 85, 0, -4, 0.7, -0.5, -60, 15, 60, 70),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.6)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        limpio = {v: [] for v in VISTAS}
        con_huesos = []
        for nombre, pose in FINALISTAS.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.5)
            m = page.evaluate(MEASURE_JS)
            s = page.evaluate(SCREEN_JS)
            print(linea(nombre, m, s, puntuar(m, s)))

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
                limpio[vista].append(
                    (nombre, recorte(page, viewer, OUT / f"{nombre}_{vista}.png", False))
                )
                if vista == "frente":
                    con_huesos.append(
                        (nombre, recorte(page, viewer, OUT / f"{nombre}_huesos.png", True))
                    )
        browser.close()

    ref = [(n, p) for n, p in [("REF foto", REF / "E_usuario.png")] if p.exists()]
    for vista, items in limpio.items():
        hoja(ref + items, OUT / f"_{vista}.png", cols=3, cell=340)
    hoja(ref + con_huesos, OUT / "_huesos.png", cols=3, cell=340)


if __name__ == "__main__":
    main()
