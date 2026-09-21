"""Ajuste fino alrededor de la candidata C antes de escribirla en el catalogo."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from final_e import VISTAS
from pose_lab_e import free_camera
from search_e10 import CAM_PROD_JS, SCREEN_JS, linea, puntuar
from search_e9 import MEASURE_JS, abrir, pose_e

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "refine_e"
REF = ROOT / "tools" / "screenshots" / "referencia"

PULGAR = dict(tcurl=0.9, taside=-0.5, t1y=-60, t1z=15, t2x=60, t3x=70)

VARIANTES = {
    "C_base": pose_e(85, 100, 20, -4, **PULGAR),
    "C_dip35": pose_e(85, 100, 35, -4, **PULGAR),
    "C_pip115": pose_e(85, 115, 20, -4, **PULGAR),
    "C_mcp95": pose_e(95, 100, 20, -4, **PULGAR),
    "C_conv-8": pose_e(85, 100, 20, -8, **PULGAR),
    "C_dip35_pip115": pose_e(85, 115, 35, -4, **PULGAR),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.6)
        viewer = page.query_selector("#viewer")

        # las metricas de pantalla solo valen desde la camara de produccion
        for nombre, pose in VARIANTES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.4)
            page.evaluate(CAM_PROD_JS)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            s = page.evaluate(SCREEN_JS)
            print(linea(nombre, m, s, puntuar(m, s)))

        free_camera(page)
        frentes = []
        for nombre, pose in VARIANTES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.4)
            hand = page.evaluate(HAND_TARGET_JS)
            t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
            orbit, fov = VISTAS["frente"]
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
            frentes.append(
                (nombre, recorte(page, viewer, OUT / f"{nombre}.png", False))
            )
        browser.close()

    ref = [(n, p) for n, p in [("REF foto", REF / "E_usuario.png")] if p.exists()]
    hoja(ref + frentes, OUT / "_frente.png", cols=4, cell=320)


if __name__ == "__main__":
    main()
