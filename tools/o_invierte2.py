"""Otras vueltas de la mano: de cabeza y del reves, sin perder el circulo."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_circulo" / "invierte"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=oinvierte2"

GIROS = {
    "x_vuelta": (-165, -80, -20),
    "z_vuelta": (15, -80, 160),
    "xz": (-165, -80, 160),
    "y180_x": (-165, 100, -20),
}


def main():
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    base = next(s for s in cat["senas"] if s["letra"] == "O")["pose"]
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_viewport_size({"width": 720, "height": 720})
        viewer = page.query_selector("#handViewer")
        for nombre, (x, y, z) in GIROS.items():
            pz = json.loads(json.dumps(base))
            pz["muneca"] = {"x": x, "y": y, "z": z}
            page.evaluate("(q) => window.__LSM_CONTROLLER__.applyTestPose(q)", pz)
            time.sleep(0.35)
            viewer.screenshot(path=str(OUT / f"{nombre}.png"))
            print(nombre)
        browser.close()


if __name__ == "__main__":
    main()
