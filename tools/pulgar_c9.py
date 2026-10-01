"""Sube el pulgar de la C otros 15-25 grados: barrido fino de RightHandThumb1.z."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import POSE_C, extra_metrics, variante

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c9"

# (tcurl, taside, Thumb1.y, Thumb1.z) — el guardado hoy es z=35
CANDIDATOS = {
    "z35_actual": (0.55, 0.20, 25, 35),
    "z45": (0.55, 0.20, 25, 45),
    "z50": (0.55, 0.20, 25, 50),
    "z55": (0.55, 0.20, 25, 55),
    "z60": (0.55, 0.20, 25, 60),
    "z50_a35": (0.55, 0.35, 25, 50),
    "z55_a35": (0.55, 0.35, 25, 55),
    "z55_c45": (0.45, 0.20, 25, 55),
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
