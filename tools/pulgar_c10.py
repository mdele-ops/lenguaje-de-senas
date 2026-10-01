"""Barrido grande del levante del pulgar de la C: de 55 hasta 115 grados."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import POSE_C, extra_metrics, variante

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c10"

# (tcurl, taside, Thumb1.y, Thumb1.z) — lo guardado ahora es z=55, aside=0.35
CANDIDATOS = {
    "z055_actual": (0.55, 0.35, 25, 55),
    "z070": (0.55, 0.35, 25, 70),
    "z085": (0.55, 0.35, 25, 85),
    "z100": (0.55, 0.35, 25, 100),
    "z115": (0.55, 0.35, 25, 115),
    "z085_c30": (0.30, 0.35, 25, 85),
    "z100_c30": (0.30, 0.35, 25, 100),
    "z100_a60": (0.55, 0.60, 25, 100),
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
            lab.apply_pose(page, variante(*params))
            m = c_lab.metrics(page, unit)
            m.update(extra_metrics(page, unit))
            print(
                f"{caso:12s} abertura={m['abertura']:.3f} dy={m['dy']:+.3f} "
                f"arriba={m['arriba']:+.3f}",
                flush=True,
            )
            for deg in ORBITS:
                out = OUT / f"{caso}_{deg:+04d}.png"
                lab.shot(page, out, orbit=f"{deg}deg 84deg {lab.RADIUS}", side="right")
                shots.append((f"{caso} {deg}deg", out))
        lab.sheet(shots, OUT / "_hoja.png", cols=4, cell=290)
        browser.close()


if __name__ == "__main__":
    main()
