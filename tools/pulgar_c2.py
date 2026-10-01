"""Sonda de ejes del pulgar de la C: mueve un parametro a la vez y mide."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c2"

BASE = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "catalogo-lsm.json").read_text(
        encoding="utf-8"
    )
)
POSE_C = next(s for s in BASE["senas"] if s["letra"] == "C")["pose"]


def variante(tcurl=None, taside=None, t1=None, t2=None, t3=None):
    pose = json.loads(json.dumps(POSE_C))
    if tcurl is not None:
        pose["thumb"]["curl"] = tcurl
    if taside is not None:
        pose["thumb"]["aside"] = taside
    if t1 is not None:
        pose["extra"]["RightHandThumb1"] = dict(t1)
    if t2 is not None:
        pose["extra"]["RightHandThumb2"] = dict(t2)
    if t3 is not None:
        pose["extra"]["RightHandThumb3"] = dict(t3)
    return pose


CASOS = {
    "base": variante(),
    "tcurl_070": variante(tcurl=0.70),
    "tcurl_100": variante(tcurl=1.0),
    "taside_030": variante(taside=0.3),
    "taside_000": variante(taside=0.0),
    "t1y_000": variante(t1={"y": 0, "z": 8}),
    "t1y_070": variante(t1={"y": 70, "z": 8}),
    "t1z_n30": variante(t1={"y": 34, "z": -30}),
    "t1z_p40": variante(t1={"y": 34, "z": 40}),
    "t1x_n40": variante(t1={"x": -40, "y": 34, "z": 8}),
    "t1x_p40": variante(t1={"x": 40, "y": 34, "z": 8}),
    "t2x_p40": variante(t2={"x": 40}),
    "t2y_p40": variante(t2={"y": 40}),
    "t2z_p40": variante(t2={"z": 40}),
    "t2z_n40": variante(t2={"z": -40}),
}


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
            print(f"{caso:12s} abertura={m['abertura']:.3f} dy={m['dy']:+.3f} "
                  f"hueco_x={m['hueco_x']:+.3f} juntos={m['juntos']:.3f}", flush=True)
            out = OUT / f"{caso}.png"
            lab.shot(page, out, orbit=f"30deg 84deg {lab.RADIUS}", side="right")
            shots.append((caso, out))
        lab.sheet(shots, OUT / "_hoja.png", cols=5, cell=260)
        browser.close()


if __name__ == "__main__":
    main()
