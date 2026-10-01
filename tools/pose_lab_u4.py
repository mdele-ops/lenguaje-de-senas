"""U lab 4: apretar mas los dos dedos largos, en paralelo."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_u import linea, pose_u
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_u4"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lab_u2" / "_ref.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=u4"

CASOS = {
    "z8": pose_u(iz=8, mz=-8, arm_z=0),
    "z10": pose_u(iz=10, mz=-10, arm_z=0),
    "z12": pose_u(iz=12, mz=-12, arm_z=0),
    "p10": pose_u(iz=10, mz=-12, iz2=-6, mz2=6, arm_z=0),
    "p12": pose_u(iz=12, mz=-14, iz2=-8, mz2=8, arm_z=0),
    "p14": pose_u(iz=14, mz=-16, iz2=-9, mz2=9, arm_z=0),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        free_camera(page)
        items = [("REF foto", REF)] if REF.exists() else []
        for nombre, pose in CASOS.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(" ", linea(nombre, m), f"dC={abs(m['cruce']-m['crucePip']):.3f}")
            encuadrar(page, 0)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, MANO, margen=0.22, lado=520)
            items.append((nombre, ruta))
        browser.close()
    hoja(items, OUT / "_hoja.png", cols=3, cell=380, titulo="U · mas juntas")


if __name__ == "__main__":
    main()
