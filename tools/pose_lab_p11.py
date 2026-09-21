"""P lab 11: finalistas de la P, con el cuadro completo de produccion.

Al doblar la muñeca la mano baja y se recorta contra el chaleco, asi que aqui
se comparan los tres mejores angulos del lab 10 y, para cada uno, la posicion
del brazo: interesa que el puno y los dos dedos queden sobre el fondo oscuro,
que es donde se leen.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM
from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET, hoja
from pose_lab_p9 import MEASURE_JS
from pose_lab_p10 import pose_p10
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p11"
OUT.mkdir(parents=True, exist_ok=True)
FOTO = ROOT / "tools" / "screenshots" / "ref_P_zoom.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p11"

ANGULOS = {
    # (mid_mcp, wy, ex_x, ex_y): los tres que mejor clavan los angulos de la foto
    "A": dict(mid_mcp=55, wy=95, ex_x=22, ex_y=10),
    "B": dict(mid_mcp=55, wy=90, ex_x=26, ex_y=10),
    "C": dict(mid_mcp=48, wy=100, ex_x=26, ex_y=10),
}

CASES = {}
for clave, ang in ANGULOS.items():
    for arm in (-30, -38):
        CASES[f"{clave}_arm{arm}"] = pose_p10(arm_z=arm, **ang)
# subir el brazo para despegar la mano del chaleco
for clave, ang in ANGULOS.items():
    pose = pose_p10(arm_z=-34, **ang)
    pose["extra"][ARM] = {"z": -34, "x": -12}
    CASES[f"{clave}_arriba"] = pose


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.5)
        viewer = page.query_selector("#viewer")
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
        time.sleep(0.4)

        cuadro, cerca = [], []
        if FOTO.exists():
            cerca.append(("REF foto", FOTO))
        for name, pose in CASES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:12s} idx={m['idxAng']:+6.1f} mid={m['midAng']:+6.1f} "
                f"esc={m['escuadra']:5.1f} palmNz={m['palmNz']:+.2f} "
                f"scr={m['idxScr']:.2f}/{m['midScr']:.2f} mano={m['manoAng']:+6.1f}"
            )
            path = OUT / f"{name}.png"
            viewer.screenshot(path=str(path))
            cuadro.append((name, path))
            cerca.append((name, path))

        browser.close()

    hoja(cuadro, OUT / "_cuadro.png", cols=3, cell=360)
    hoja(cerca, OUT / "_cerca.png", cols=4, cell=330, caja=(215, 70, 435, 290))
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
