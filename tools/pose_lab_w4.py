"""W lab 4: equilibrar los dos huecos del tridente en pantalla.

Con solo spread, el indice abre ~34 deg en pantalla y el anular se queda en
~22 aunque el 3D ya sea mayor. Se prueba correr el medio hacia el indice
(spread negativo) y torcer el anular (extra y) para que su abertura caiga
en el plano de la camara, como pide la foto.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from enfoque_r import hoja
from pose_lab_e import BONES, T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_w import ANGLE_JS, linea, pose_w
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_w4"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "W_usuario.png"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=w4"

RING1 = BONES["ring"][0]
THUMB = {T1: {"y": -30, "z": 50}, T2: {"x": 60}}


def pose(iz=-14, mz=0, rz=32, ring=None):
    p = pose_w(iz=iz, mz=mz, rz=rz, thumb=THUMB)
    if ring:
        p["extra"][RING1] = dict(ring)
    return p


def main():
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    vieja = next(s for s in catalogo["senas"] if s["letra"] == "W")["pose"]

    casos = {
        "00_catalogo": vieja,
        "A_base": pose(),
        "B_m-6": pose(mz=-6),
        "C_m-10": pose(mz=-10),
        "D_m-8_r36": pose(mz=-8, rz=36),
        "E_ry-15": pose(ring={"y": -15}),
        "F_ry-25": pose(ring={"y": -25}),
        "G_m-8_ry-18": pose(mz=-8, ring={"y": -18}),
        "H_i12_m-8_r34": pose(iz=-12, mz=-8, rz=34),
        "I_i12_m-6_r30": pose(iz=-12, mz=-6, rz=30),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(2.0)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", REF)] if REF.exists() else []
        medidas = {}
        for nombre, pose_n in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose_n)
            time.sleep(0.4)
            m = page.evaluate(MEASURE_JS)
            a = page.evaluate(ANGLE_JS)
            medidas[nombre] = {**m, **a}
            print(" ", linea(nombre, m, a) if not m.get("error") else (nombre, m, a))
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            ruta = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(ruta))
            items.append((nombre, ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=360, titulo="W · lab 4 · equilibrio")
    (OUT / "_medidas.json").write_text(json.dumps(medidas, indent=2), encoding="utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
