"""Antes/despues del pulgar de la C: pose vieja (plana) contra la guardada ahora."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageEnhance
from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import extra_metrics

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c17"

# Pulgar tal como estaba antes de subirlo.
ANTES = {
    "thumb": {"curl": 0.42, "aside": 0.8},
    "extra": {"RightHandThumb1": {"y": 34, "z": 8}, "RightHandThumb2": None},
}

ORBITS = (0, 35)


def realza(path):
    """El visor quema la piel clara; bajar brillo y subir contraste deja ver el pulgar."""
    img = Image.open(path).convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(0.62)
    img = ImageEnhance.Contrast(img).enhance(1.9)
    img.save(path)


def poses(catalog):
    nueva = next(s for s in catalog["senas"] if s["letra"] == "C")["pose"]
    vieja = json.loads(json.dumps(nueva))
    vieja["thumb"] = ANTES["thumb"]
    vieja["extra"]["RightHandThumb1"] = ANTES["extra"]["RightHandThumb1"]
    vieja["extra"].pop("RightHandThumb2", None)
    return {"antes": vieja, "despues": nueva}


def main():
    catalog = lab.load_catalog()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)
        shots = []
        for nombre, pose in poses(catalog).items():
            lab.apply_pose(page, pose)
            m = c_lab.metrics(page, unit)
            m.update(extra_metrics(page, unit))
            print(
                f"{nombre:8s} abertura={m['abertura']:.3f} dy={m['dy']:+.3f} "
                f"arriba={m['arriba']:+.3f}",
                flush=True,
            )
            for deg in ORBITS:
                out = OUT / f"{nombre}_{deg:+04d}.png"
                lab.shot(page, out, orbit=f"{deg}deg 84deg 0.22m", side="right")
                realza(out)
                shots.append((f"{nombre.upper()} · {deg}deg", out))
        lab.sheet(shots, OUT / "_hoja.png", cols=2, cell=400)
        browser.close()


if __name__ == "__main__":
    main()
