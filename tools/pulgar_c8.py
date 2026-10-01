"""Verifica la C ya guardada en el catalogo, usando la pagina tal cual la ve el usuario."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c8"
ORBITS = (-30, 0, 30, 60)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = browser.new_page(viewport={"width": 760, "height": 760})
        page.goto(lab.URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("#anim-info", timeout=30000, state="attached")
        if not lab.poll_ready(page):
            raise RuntimeError("El modelo 3D no cargo")
        time.sleep(1.0)

        pose = page.evaluate("() => window.__LSM_CONTROLLER__.getSena('C').pose")
        print("pulgar servido por el catalogo:", pose["thumb"], pose["extra"]["RightHandThumb1"])
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('C')")
        time.sleep(2.6)

        shots = []
        for deg in ORBITS:
            out = OUT / f"orbit_{deg:+04d}.png"
            lab.shot(page, out, orbit=f"{deg}deg 84deg {lab.RADIUS}", side="right")
            shots.append((f"{deg}deg", out))
        lab.sheet(shots, OUT / "_hoja.png", cols=4, cell=300)
        browser.close()


if __name__ == "__main__":
    main()
