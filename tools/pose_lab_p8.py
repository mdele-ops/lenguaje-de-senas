"""P lab 8: ajuste final con la mano ya de perfil.

Con la muñeca a ~95 los dos dedos se ven a su largo completo (midScr pasa de
0.66 a 0.94). Quedan tres cosas por cerrar:

  - el pulgar, que en esta orientacion cuelga por debajo y hace parecer la mano
    una garra; tiene que recogerse contra la base del medio.
  - el reparto del giro: todo en la muñeca puede retorcer la piel, asi que se
    prueba tambien con parte del giro en el antebrazo.
  - donde queda la mano: si el dedo medio se mete sobre el chaleco se pierde
    contraste, asi que se prueba separando el brazo del cuerpo.

Todas las capturas son con la camara real de practica.html, recortadas a la
mano.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_p import REF
from pose_lab_p7 import (
    CAM_FOV,
    CAM_ORBIT,
    CAM_TARGET,
    MEASURE_JS,
    hoja,
    pose_p7,
)
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p8"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p8"

CASES = {
    "00_wy95": pose_p7(wy=95),
    # --- pulgar recogido para que no cuelgue ------------------------------
    "A_t_cerrado": pose_p7(wy=95, tcurl=0.95, t1y=-85),
    "B_t_y-60": pose_p7(wy=95, tcurl=0.85, t1y=-60),
    "C_t_y-100": pose_p7(wy=95, tcurl=0.85, t1y=-100),
    "D_t_as0": pose_p7(wy=95, tcurl=0.85, taside=0.0, t1y=-85),
    "E_t_t2_50": pose_p7(wy=95, tcurl=0.85, t1y=-85, t2x=50),
    # --- reparto del giro entre antebrazo y muñeca ------------------------
    "F_wy60_fz-35": pose_p7(wy=60, tcurl=0.85, t1y=-85, fore={"z": -35}),
    "G_wy75_fz-20": pose_p7(wy=75, tcurl=0.85, t1y=-85, fore={"z": -20}),
    # --- inclinacion fina y posicion del brazo ----------------------------
    "H_wz20": pose_p7(wy=95, wz=20, tcurl=0.85, t1y=-85),
    "I_wz0": pose_p7(wy=95, wz=0, tcurl=0.85, t1y=-85),
    "J_arm-30": pose_p7(wy=95, tcurl=0.85, t1y=-85, arm_z=-30),
    "K_arm-8": pose_p7(wy=95, tcurl=0.85, t1y=-85, arm_z=-8),
}


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

        items = [("REF lamina", REF)] if REF.exists() else []
        for name, pose in CASES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:14s} palmN=({m['palmNx']:+.2f},{m['palmNz']:+.2f}) "
                f"midSide={m['midSide']:+.2f} ang={m['escuadra']:5.1f} "
                f"idxScr={m['idxScr']:.2f} midScr={m['midScr']:.2f}"
            )
            path = OUT / f"{name}.png"
            viewer.screenshot(path=str(path))
            items.append((name, path))

        browser.close()

    hoja(items, OUT / "_produccion.png", cols=4, cell=330, caja=(215, 65, 415, 265))
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
