"""Fotos de los mejores candidatos del pulgar de la C, de frente y en tres cuartos."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import POSE_C, variante

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c5"

CANDIDATOS = {
    "actual": None,
    "A_c40_a70_y25_z35": (0.40, 0.70, 25, 35),
    "B_c55_a20_y25_z35": (0.55, 0.20, 25, 35),
    "C_c40_a20_y40_z35": (0.40, 0.20, 40, 35),
    "D_c55_a45_y25_z45": (0.55, 0.45, 25, 45),
    "E_c55_a70_y10_z35": (0.55, 0.70, 10, 35),
    "F_c25_a70_y40_z35": (0.25, 0.70, 40, 35),
    "G_c40_a45_y40_z35": (0.40, 0.45, 40, 35),
}

ORBITS = (0, 30)


def main():
    catalog = lab.load_catalog()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)
        shots = []
        for caso, params in CANDIDATOS.items():
            pose = POSE_C if params is None else variante(*params)
            lab.apply_pose(page, pose)
            m = c_lab.metrics(page, unit)
            print(f"{caso:20s} abertura={m['abertura']:.3f} dy={m['dy']:+.3f}", flush=True)
            for deg in ORBITS:
                out = OUT / f"{caso}_{deg:+04d}.png"
                lab.shot(page, out, orbit=f"{deg}deg 84deg {lab.RADIUS}", side="right")
                shots.append((f"{caso} {deg}deg", out))
        lab.sheet(shots, OUT / "_hoja.png", cols=4, cell=280)
        browser.close()


if __name__ == "__main__":
    main()
