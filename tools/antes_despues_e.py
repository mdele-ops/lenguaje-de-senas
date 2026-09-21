"""Antes / despues de la E: pose anterior del catalogo contra la que quedo,
por el camino de produccion, con y sin huesos proyectados."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from pose_lab_e import ARM, BONES, FINGERS, T1, T2, T3, free_camera
from search_e10 import CAM_PROD_JS, SCREEN_JS, linea, puntuar
from search_e9 import MEASURE_JS, abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "antes_despues_e"
REF = ROOT / "tools" / "screenshots" / "referencia"

# Pose que estaba en el catalogo antes de este arreglo: el doblez se reparte a
# mano con un `extra` por articulacion (nudillo 85 -> media 100 -> distal 20).
# La ultima falange queda casi recta, asi que el dedo entero sale por delante de
# la palma con la yema apuntando al frente: la garra que se veia en la app.
ANTES = {
    "thumb": {"curl": 0.9, "aside": -0.5},
    "index": {"curl": 0.0, "spread": 12},
    "middle": {"curl": 0.0, "spread": 4},
    "ring": {"curl": 0.0, "spread": -4},
    "pinky": {"curl": 0.0, "spread": -12},
    "extra": {
        **{BONES[f][0]: {"x": 85} for f in FINGERS},
        **{BONES[f][1]: {"x": 100} for f in FINGERS},
        **{BONES[f][2]: {"x": 20} for f in FINGERS},
        T1: {"y": -60, "z": 15},
        T2: {"x": 60},
        T3: {"x": 70},
        ARM: {"z": -18},
    },
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.6)
        viewer = page.query_selector("#viewer")

        despues = page.evaluate("() => window.__LSM_CONTROLLER__.getSena('E').pose")
        casos = {"ANTES": ANTES, "DESPUES": despues}

        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.4)
            page.evaluate(CAM_PROD_JS)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            s = page.evaluate(SCREEN_JS)
            print(linea(nombre, m, s, puntuar(m, s)))

        free_camera(page)
        limpio, huesos = [], []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.4)
            hand = page.evaluate(HAND_TARGET_JS)
            t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
            for _ in range(2):
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = '0deg 84deg 1.15m';
                        mv.fieldOfView = '14deg';
                        mv.jumpCameraToGoal();
                    }""",
                    {"t": t},
                )
                time.sleep(0.3)
            limpio.append((nombre, recorte(page, viewer, OUT / f"{nombre}.png", False)))
            huesos.append(
                (nombre, recorte(page, viewer, OUT / f"{nombre}_huesos.png", True))
            )
        browser.close()

    ref = [(n, p) for n, p in [("REF foto", REF / "E_usuario.png")] if p.exists()]
    hoja(ref + limpio + huesos, OUT / "_antes_despues.png", cols=3, cell=340)


if __name__ == "__main__":
    main()
