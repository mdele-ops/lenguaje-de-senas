"""U lab 2: capturas nitidas con el encuadre de dedos arriba.

El lab 1 midio que z6 junta sin cruzar (cruce=-0.39, yemas=0.18) y z10 ya
roza el cruce. Aqui se mira eso de cerca, con y sin el pulgar de la R, y con
la camara pegada a muneca+yema como en eje_r (si no, el recorte sale borroso
y de lado).
"""
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from eje_r import encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_u import linea, pose_u
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_u2"
OUT.mkdir(parents=True, exist_ok=True)
REF_SRC = ROOT / "tools" / "screenshots" / "referencia" / "U_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=u2"


def ref_mano(lado=560):
    im = Image.open(REF_SRC).convert("RGB")
    w, h = im.size
    # recorta el cartel "Uu" de abajo
    im = im.crop((0, 0, w, int(h * 0.78)))
    ruta = OUT / "_ref.png"
    im.resize((lado, lado), Image.LANCZOS).save(ruta)
    return ruta


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    u_vieja = next(s for s in catalogo["senas"] if s["letra"] == "U")["pose"]

    casos = {
        "00_catalogo": u_vieja,
        "01_z8_sinPulgar": pose_u(
            iz=8, mz=-8, tcurl=0.55, taside=0.0, thumb={}, arm_z=0
        ),
        "02_soloPulgarR": pose_u(iz=0, mz=0, arm_z=0),
        "03_z6_pulgarR": pose_u(iz=6, mz=-6, arm_z=0),
        "04_z8_pulgarR": pose_u(iz=8, mz=-8, arm_z=0),
        "05_z10_pulgarR": pose_u(iz=10, mz=-10, arm_z=0),
        "06_z8_arm": pose_u(iz=8, mz=-8, arm_z=-18),
        "07_z8_t1y60": pose_u(
            iz=8,
            mz=-8,
            arm_z=0,
            thumb={T1: {"y": -60, "z": 40}, T2: {"x": 60}},
        ),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", ref_mano())]
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.32)
            m = page.evaluate(MEASURE_JS)
            print(" ", linea(nombre, m) if not m.get("error") else (nombre, m))
            encuadrar(page, 0)
            ruta = OUT / f"{nombre}_frente.png"
            captura(page, ruta, MANO, margen=0.22, lado=520)
            items.append((nombre, ruta))
            visor = OUT / f"{nombre}_visor.png"
            viewer.screenshot(path=str(visor))
            items.append((nombre + " visor", visor))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=400, titulo="U · lab 2 nitido")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
