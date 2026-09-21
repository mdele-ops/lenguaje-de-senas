"""U lab 3: candidatas mas juntas, vistas como las ve el usuario.

La busqueda 1 se quedo en cruce ~-0.75 (todavia hay hueco). Aqui se aprietan
mas los dos dedos y se capturan dos cosas: el visor de produccion (lo que
sale en practica.html) y el recorte de la mano.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_u import linea, pose_u
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_u3"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lab_u2" / "_ref.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=u3"


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}

    casos = {
        "00_catalogo": por["U"],
        "01_z6": pose_u(iz=6, mz=-6, arm_z=-18),
        "02_z8": pose_u(iz=8, mz=-8, arm_z=-18),
        "03_par7_9": pose_u(iz=7, mz=-9, iz2=-5, mz2=5, arm_z=-18),
        "04_par9_9": pose_u(iz=9, mz=-9, iz2=-5, mz2=5, arm_z=-18),
        "05_par11_11": pose_u(iz=11, mz=-11, iz2=-6, mz2=6, arm_z=-18),
        "06_par12_12": pose_u(iz=12, mz=-12, iz2=-8, mz2=8, arm_z=-18),
        "07_R": por["R"],
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", REF)] if REF.exists() else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            extra = ""
            if not m.get("error"):
                extra = f" dC={abs(m['cruce']-m.get('crucePip', m['cruce'])):.3f}"
                print(" ", linea(nombre, m) + extra)
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            visor = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(visor))
            items.append((nombre + " prod", visor))
            encuadrar(page, 0)
            ruta = OUT / f"{nombre}_mano.png"
            captura(page, ruta, MANO, margen=0.22, lado=520)
            items.append((nombre + " mano", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=380, titulo="U · lab 3 mas juntas")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
