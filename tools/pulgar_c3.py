"""Barrido del pulgar de la C alrededor de RightHandThumb1.z (el eje que lo sube)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c3"

BASE = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "catalogo-lsm.json").read_text(
        encoding="utf-8"
    )
)
POSE_C = next(s for s in BASE["senas"] if s["letra"] == "C")["pose"]


def variante(tcurl=0.42, taside=0.8, z=8, y=34, x=None, t2=None):
    pose = json.loads(json.dumps(POSE_C))
    pose["thumb"] = {"curl": tcurl, "aside": taside}
    t1 = {"y": y, "z": z}
    if x:
        t1["x"] = x
    pose["extra"]["RightHandThumb1"] = t1
    if t2:
        pose["extra"]["RightHandThumb2"] = dict(t2)
    return pose


CASOS = {}
for z in (40, 55, 70):
    for taside in (0.4, 0.8):
        CASOS[f"z{z}_a{int(taside*10):02d}"] = variante(z=z, taside=taside)
CASOS["z55_a04_c60"] = variante(z=55, taside=0.4, tcurl=0.6)
CASOS["z55_a04_c20"] = variante(z=55, taside=0.4, tcurl=0.2)
CASOS["z70_a04_c20"] = variante(z=70, taside=0.4, tcurl=0.2)
CASOS["z55_a04_t2z30"] = variante(z=55, taside=0.4, t2={"z": 30})
CASOS["z55_a04_y10"] = variante(z=55, taside=0.4, y=10)
CASOS["z55_a04_y60"] = variante(z=55, taside=0.4, y=60)


def main():
    catalog = lab.load_catalog()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)
        shots = []
        for caso, pose in CASOS.items():
            lab.apply_pose(page, pose)
            m = c_lab.metrics(page, unit)
            print(f"{caso:16s} abertura={m['abertura']:.3f} dy={m['dy']:+.3f} "
                  f"hueco_x={m['hueco_x']:+.3f}", flush=True)
            out = OUT / f"{caso}.png"
            lab.shot(page, out, orbit=f"30deg 84deg {lab.RADIUS}", side="right")
            shots.append((caso, out))
        lab.sheet(shots, OUT / "_hoja.png", cols=4, cell=260)
        browser.close()


if __name__ == "__main__":
    main()
