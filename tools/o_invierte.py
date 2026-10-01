"""Compara la O actual con la mano dada vuelta."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_circulo" / "invierte"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=oinvierte"

# La actual es x15 y-80 z-20. La vuelta es el mismo giro mas 180 en el eje
# que presenta el otro lado de la mano.
GIROS = {
    "actual": (15, -80, -20),
    "vuelta_y": (15, 100, -20),
    "signos": (-15, 80, 20),
    "y_opuesta": (15, 80, -20),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
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
            time.sleep(0.4)
            viewer.screenshot(path=str(OUT / f"{nombre}.png"))
            print(nombre, x, y, z)
        browser.close()


if __name__ == "__main__":
    main()
