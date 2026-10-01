"""Comparativa final del pulgar de la C con la camara real de practica.html."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image
from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import POSE_C, variante

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c7"

CANDIDATOS = {
    "0_actual": None,
    "1_c40_a45_y40_z35": (0.40, 0.45, 40, 35),
    "2_c35_a30_y40_z35": (0.35, 0.30, 40, 35),
    "3_c55_a20_y25_z35": (0.55, 0.20, 25, 35),
    "4_c35_a60_y40_z35": (0.35, 0.60, 40, 35),
    "5_c40_a70_y25_z35": (0.40, 0.70, 25, 35),
}

VISTAS = {
    "app": ("-0.06m 1.35m 0.17m", "0deg 78deg 0.52m", "26deg"),
    "lado": ("-0.06m 1.35m 0.17m", "35deg 78deg 0.52m", "26deg"),
}


def foto(page, path, target, orbit, fov):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.target;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"target": target, "orbit": orbit, "fov": fov},
    )
    time.sleep(0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    page.query_selector("#viewer").screenshot(path=str(path))
    img = Image.open(path)
    lado = min(img.size)
    left = (img.width - lado) // 2
    top = (img.height - lado) // 2
    img.crop((left, top, left + lado, top + lado)).save(path)


def main():
    catalog = lab.load_catalog()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        shots = []
        for caso, params in CANDIDATOS.items():
            lab.apply_pose(page, POSE_C if params is None else variante(*params))
            for vista, (target, orbit, fov) in VISTAS.items():
                out = OUT / f"{caso}_{vista}.png"
                foto(page, out, target, orbit, fov)
                shots.append((f"{caso} {vista}", out))
            print("  ", caso, flush=True)
        lab.sheet(shots, OUT / "_hoja.png", cols=4, cell=300)
        browser.close()


if __name__ == "__main__":
    main()
