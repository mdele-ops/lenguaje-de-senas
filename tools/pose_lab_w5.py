"""W lab 5: cerrar el tridente; la foto pide huecos visibles, no un abanico.

El catalogo actual (index -14 / ring +20) deja el indice a ~35 deg en
pantalla, mas abierto que la V. La lamina muestra tres palitos verticales
con un hueco claro pero modesto entre vecinos. Se baja el spread del indice
y se busca el anular que deje los dos huecos parecidos.
"""
import json
import shutil
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
OUT = ROOT / "tools" / "screenshots" / "lab_w5"
OUT.mkdir(parents=True, exist_ok=True)
REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images_image-1a712c26-9668-4f73-b691-e1f071b8e80a.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "W_usuario.png"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=w5"

THUMB = {T1: {"y": -30, "z": 50}, T2: {"x": 60}}


def pose(iz, rz, mz=0):
    return pose_w(iz=iz, mz=mz, rz=rz, thumb=THUMB)


def asegurar_ref():
    REF.parent.mkdir(parents=True, exist_ok=True)
    if REF_SRC.exists():
        shutil.copy2(REF_SRC, REF)
    return REF if REF.exists() else None


def main():
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    vieja = next(s for s in catalogo["senas"] if s["letra"] == "W")["pose"]

    casos = {
        "00_catalogo": vieja,
        "A_i8_r16": pose(-8, 16),
        "B_i6_r14": pose(-6, 14),
        "C_i6_r12": pose(-6, 12),
        "D_i4_r10": pose(-4, 10),
        "E_i8_r12": pose(-8, 12),
        "F_i5_r12": pose(-5, 12),
        "G_i8_r18": pose(-8, 18),
        "H_i10_r14": pose(-10, 14),
        "I_i6_r16": pose(-6, 16),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(2.0)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        ref = asegurar_ref()
        items_prod = [("REF foto", ref)] if ref else []
        items_zoom = [("REF foto", ref)] if ref else []
        medidas = {}
        for nombre, pose_n in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose_n)
            time.sleep(0.4)
            m = page.evaluate(MEASURE_JS)
            a = page.evaluate(ANGLE_JS)
            medidas[nombre] = {**m, **a}
            print(" ", linea(nombre, m, a) if not m.get("error") else (nombre, m, a))

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            prod = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(prod))
            items_prod.append((nombre, prod))

            encuadrar(page, 0, holgura=3.4)
            zoom = OUT / f"{nombre}_zoom.png"
            viewer.screenshot(path=str(zoom))
            items_zoom.append((nombre, zoom))

        browser.close()

    hoja(items_prod, OUT / "_hoja_prod.png", cols=4, cell=360, titulo="W · lab 5 · cerrar")
    hoja(items_zoom, OUT / "_hoja_zoom.png", cols=4, cell=360, titulo="W · lab 5 · zoom")
    (OUT / "_medidas.json").write_text(json.dumps(medidas, indent=2), encoding="utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
