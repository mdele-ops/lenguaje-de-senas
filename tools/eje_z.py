"""Z: jacobiano en PANTALLA. Que hueso mueve la yema a la derecha o arriba.

El trazo se lee en la foto, no en ejes de mundo: hay que saber cuanto se
desplaza la punta del indice en pixeles del visor por cada grado.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import CAJA_JS
from pose_lab_e import ARM, free_camera
from pose_lab_x2 import FOREARM
from pose_lab_z import aplicar, cam, con_extra, pose_z, abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "eje_z"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=ejez"

TIP = ["mixamorig1RightHandIndex4_043"]
PASO = 12
EJES = [
    (FOREARM, "x"),
    (FOREARM, "z"),
    (FOREARM, "y"),
    (ARM, "x"),
    (ARM, "y"),
    (ARM, "z"),
]


def punta(page):
    caja = page.evaluate(CAJA_JS, TIP)
    if caja.get("error"):
        return caja
    return {
        "x": (caja["x0"] + caja["x1"]) / 2,
        "y": (caja["y0"] + caja["y1"]) / 2,
        "w": caja["w"],
        "h": caja["h"],
    }


def main():
    base = pose_z()
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        cam(page)
        viewer = page.query_selector("#viewer")

        aplicar(page, base)
        cam(page)
        origen = punta(page)
        print(f"origen px=({origen['x']:.1f},{origen['y']:.1f}) visor={origen['w']:.0f}x{origen['h']:.0f}")
        viewer.screenshot(path=str(OUT / "00_base.png"))

        jac = {}
        print(f"{'hueso':34s} {'eje':4s} {'dpx':>8s} {'dpy':>8s}  (por grado)")
        for hueso, eje in EJES:
            aplicar(page, con_extra(base, hueso, eje, PASO))
            cam(page)
            m = punta(page)
            dpx = (m["x"] - origen["x"]) / PASO
            dpy = (m["y"] - origen["y"]) / PASO
            jac[f"{hueso}.{eje}"] = {"dpx": dpx, "dpy": dpy}
            corto = hueso.replace("mixamorig1Right", "")
            print(f"{corto:34s} {eje:4s} {dpx:+8.2f} {dpy:+8.2f}")
            viewer.screenshot(path=str(OUT / f"{corto}_{eje}{PASO:+d}.png"))

        browser.close()

    (OUT / "_jac.json").write_text(
        json.dumps({"origen": origen, "paso": PASO, "jac": jac}, indent=2),
        encoding="utf-8",
    )
    print("->", OUT)


if __name__ == "__main__":
    main()
