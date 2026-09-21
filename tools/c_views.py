"""Renderiza la C del catalogo en disco desde varias orbitas, con encuadre automatico.

Sirve para decidir desde que angulo se lee el arco y comparar con la foto de referencia.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

import lab

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "c_views"

ORBITS = [-60, -30, 0, 30, 60, 90, 120, 150]


def main():
    catalog = lab.load_catalog()
    sena = next(s for s in catalog["senas"] if s["letra"] == "C")
    print("pose C en disco:", sena["pose"])

    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=lab.CHROME_ARGS)
        page = lab.open_lab(browser, catalog)
        lab.apply_pose(page, sena["pose"])

        shots = []
        for deg in ORBITS:
            out = OUT / f"orbit_{deg:+04d}.png"
            lab.shot(page, out, orbit=f"{deg}deg 84deg {lab.RADIUS}", side="right")
            shots.append((f"{deg}deg", out))
            print("  ", deg, flush=True)

        lab.sheet(shots, OUT / "_hoja.png", cols=4, cell=260)
        browser.close()


if __name__ == "__main__":
    main()
