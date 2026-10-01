"""Comparacion final de la C: finalistas en primer plano y en el encuadre de la app."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image

import c_lab
import lab
from c_lab import T1, T3

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "ref_c" / "ref_c_original.png"
OUT = ROOT / "tools" / "screenshots" / "c_final"

BASE = dict(curl=0.26, knuckle=20, mid=34, taside=0.8, wy=90, wz=0)

FINALISTAS = {
    "A_d12_pulgar_base": c_lab.build(dist=12, tcurl=0.42, thumb={T1: {"y": 34, "z": 8}}, **BASE),
    "B_d0_pulgar_base": c_lab.build(dist=0, tcurl=0.42, thumb={T1: {"y": 34, "z": 8}}, **BASE),
    "C_d12_pulgar_punta": c_lab.build(
        dist=12, tcurl=0.42, thumb={T1: {"y": 34, "z": -6}, T3: {"x": -18}}, **BASE
    ),
    "D_d12_sin_brazo": c_lab.build(
        dist=12, tcurl=0.42, thumb={T1: {"y": 34, "z": 8}}, arm={}, **BASE
    ),
    "E_m38_d0": c_lab.build(
        curl=0.26, knuckle=20, mid=38, dist=0, tcurl=0.38, taside=0.7,
        thumb={T1: {"y": 34, "z": 8}}, wy=90, wz=0,
    ),
    "F_actual_en_disco": next(
        s for s in lab.load_catalog()["senas"] if s["letra"] == "C"
    )["pose"],
}

APP_TARGET = "0m 2.45m 0.15m"
APP_ORBIT = "0deg 84deg 2.5m"
APP_FOV = "30deg"


def app_shot(page, path):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.o;
            mv.fieldOfView = a.f;
            mv.jumpCameraToGoal();
        }""",
        {"t": APP_TARGET, "o": APP_ORBIT, "f": APP_FOV},
    )
    time.sleep(0.35)
    page.query_selector("#viewer").screenshot(path=str(path))
    img = Image.open(path)
    s = min(img.size)
    img.crop(((img.width - s) // 2, 0, (img.width - s) // 2 + s, s)).save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = lab.load_catalog()

    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)

        cerca, lejos = [], []
        for name, pose in FINALISTAS.items():
            lab.apply_pose(page, pose)
            m = c_lab.metrics(page, unit)
            print(f"{name}: abertura={m['abertura']:.2f} cuerda={m['cuerda']:.2f} "
                  f"dy={m['dy']:+.2f} palmaX={m['palma_x']:+.2f}", flush=True)

            near = OUT / f"cerca_{name}.png"
            lab.shot(page, near, orbit=f"0deg 84deg 0.32m", side="right")
            cerca.append((name, near))

            far = OUT / f"app_{name}.png"
            app_shot(page, far)
            lejos.append((name, far))

        browser.close()

    lab.sheet([("REFERENCIA", REF)] + cerca, OUT / "_cerca.png", cols=4, cell=340)
    lab.sheet([("REFERENCIA", REF)] + lejos, OUT / "_app.png", cols=4, cell=340)


if __name__ == "__main__":
    main()
