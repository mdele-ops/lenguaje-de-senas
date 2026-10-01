"""Ajuste fino: mano de lado y el circulo mirando a la persona."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_circulo" / "lado"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=olado2"

GIROS = [
    (15, -80, -20),
    (5, -75, -10),
    (25, -85, -30),
    (10, -70, -15),
    (20, -90, -10),
    (0, -80, -25),
]


def main():
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    base = next(s for s in cat["senas"] if s["letra"] == "O")["pose"]
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_viewport_size({"width": 720, "height": 720})
        viewer = page.query_selector("#handViewer")
        for x, y, z in GIROS:
            pz = json.loads(json.dumps(base))
            pz["muneca"] = {"x": x, "y": y, "z": z}
            page.evaluate("(q) => window.__LSM_CONTROLLER__.applyTestPose(q)", pz)
            time.sleep(0.35)
            nombre = f"b_x{x}_y{y}_z{z}.png"
            viewer.screenshot(path=str(OUT / nombre))
            print(nombre)
        browser.close()


if __name__ == "__main__":
    main()
