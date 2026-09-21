"""X lab 3: gancho mas cerrado y jalon diagonal de antebrazo (x+, z-).

Sobre la pose de perfil, ForeArm.x mueve a la derecha y ForeArm.z negativo
sube la mano: juntos dibujan la flecha arriba-derecha de la lamina sin
doblar la muneca.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, _GET_SCENE, free_camera
from pose_lab_x import MEASURE_JS, REF, pose_x, asegurar_ref, linea
from pose_lab_x2 import FOREARM, POS_JS, cam
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x3"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x3"

WY, WX = 72, -10
ARM_Z = -18
T1 = "mixamorig1RightHandThumb1_036"


def pose_base(mcp=32, pip=78, dip=50, tcurl=0.55, fx=0, fz=0, t1y=-18):
    pose = pose_x(
        mcp=mcp, pip=pip, dip=dip, tcurl=tcurl, taside=0.1,
        wy=WY, wx=WX, arm_z=ARM_Z, t1={"y": t1y},
    )
    pose["extra"][FOREARM] = {"x": fx, "z": fz}
    return pose


def main():
    ref = asegurar_ref()
    formas = {
        "00_recto": pose_base(mcp=26, pip=68, dip=40),
        "01_gancho": pose_base(),
        "02_duro": pose_base(mcp=36, pip=86, dip=56),
        "03_tcurl65": pose_base(tcurl=0.65),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", ref)] if ref else []
        for nombre, pose in formas.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            m = page.evaluate(MEASURE_JS)
            print(" ", linea(nombre, m))
            cam(page)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, huesos=MANO, margen=0.42, lado=420)
            items.append((nombre, ruta))
        hoja(items, OUT / "_forma.png", cols=3, cell=360, titulo="X · gancho")

        base = pose_base()
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", base)
        time.sleep(0.25)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]

        pasos = [
            (0.0, 0, 0),
            (0.25, 4, -4),
            (0.5, 8, -8),
            (0.75, 11, -11),
            (1.0, 14, -14),
        ]
        puntos = []
        tira = []
        print("jalon ForeArm x+ / z-")
        for t, fx, fz in pasos:
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                pose_base(fx=fx, fz=fz),
            )
            time.sleep(0.22)
            m = page.evaluate(POS_JS)
            dx = (m["x"] - origen["x"]) / palm
            dy = (m["y"] - origen["y"]) / palm
            dz = (m["z"] - origen["z"]) / palm
            puntos.append((dx, dy))
            print(f"  t={t:.2f} fx={fx:+3d} fz={fz:+3d}  d=({dx:+.3f},{dy:+.3f},{dz:+.3f})")
            cam(page)
            ruta = OUT / f"mov_{int(t*100):03d}.png"
            captura(page, ruta, huesos=MANO, margen=0.55, lado=420)
            tira.append((f"t={t:.2f}", ruta))
            viewer.screenshot(path=str(OUT / f"prod_{int(t*100):03d}.png"))

        hoja(
            ([("REF foto", ref)] if ref else []) + tira,
            OUT / "_mov.png",
            cols=3,
            cell=360,
            titulo="X · jalon diagonal",
        )

        lienzo = Image.new("RGB", (420, 420), (255, 255, 255))
        draw = ImageDraw.Draw(lienzo)
        draw.line([(30, 390), (390, 390)], fill=(200, 200, 200), width=1)
        draw.line([(30, 390), (30, 30)], fill=(200, 200, 200), width=1)
        esc = 280
        pix = [(30 + (x + 0.05) * esc, 390 - (y + 0.05) * esc) for x, y in puntos]
        if len(pix) > 1:
            draw.line(pix, fill=(150, 20, 60), width=5)
        for i, (px, py) in enumerate(pix):
            draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(150, 20, 60))
            draw.text((px + 8, py - 6), str(i), fill=(40, 40, 40))
        lienzo.save(OUT / "_trazo.png")
        print("trazo", OUT / "_trazo.png")

        browser.close()


if __name__ == "__main__":
    main()
