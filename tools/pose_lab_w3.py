"""W lab 3: vistas de produccion para elegir abertura del tridente.

El recorte cercano del lab 1/2 subia pixeles de una mano minuscula y no se
podia juzgar. Aqui se captura el visor entero en la camara de produccion
(como la V) y un zoom nativo con encuadrar, sin reescalar.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import hoja
from pose_lab_e import T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_w import ANGLE_JS, linea, pose_w
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_w3"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "W_usuario.png"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=w3"


def main():
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    vieja = next(s for s in catalogo["senas"] if s["letra"] == "W")["pose"]

    casos = {
        "00_catalogo": vieja,
        "A_i14_r20": pose_w(iz=-14, rz=20),
        "B_i14_r28": pose_w(iz=-14, rz=28),
        "C_i14_r36": pose_w(iz=-14, rz=36),
        "D_i12_r32": pose_w(iz=-12, rz=32),
        "E_i16_r32": pose_w(iz=-16, rz=32),
        "F_i14_r32_t50": pose_w(
            iz=-14, rz=32, thumb={T1: {"y": -30, "z": 50}, T2: {"x": 60}}
        ),
        "G_i14_r32": pose_w(iz=-14, rz=32),
        "H_i10_r24": pose_w(iz=-10, rz=24),
        "I_i18_r40": pose_w(iz=-18, rz=40),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(2.2)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items_prod = [("REF foto", REF)] if REF.exists() else []
        items_zoom = [("REF foto", REF)] if REF.exists() else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.45)
            m = page.evaluate(MEASURE_JS)
            a = page.evaluate(ANGLE_JS)
            medidas[nombre] = {**m, **a}
            print(" ", linea(nombre, m, a) if not m.get("error") else (nombre, m, a))

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            prod = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(prod))
            items_prod.append((nombre, prod))

            encuadrar(page, 0, holgura=2.2)
            zoom = OUT / f"{nombre}_zoom.png"
            viewer.screenshot(path=str(zoom))
            items_zoom.append((nombre, zoom))

        browser.close()

    hoja(items_prod, OUT / "_hoja_prod.png", cols=4, cell=360, titulo="W · lab 3 · produccion")
    hoja(items_zoom, OUT / "_hoja_zoom.png", cols=4, cell=360, titulo="W · lab 3 · zoom mano")
    (OUT / "_medidas.json").write_text(
        json.dumps(medidas, indent=2), encoding="utf-8"
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
