"""La O de lado, con el agujero mirando a la persona.

La forma de indice y pulgar no cambia. Solo se prueba el giro de la muneca
para que, en la camara de la pagina, se vea el circulo de frente y la mano
de perfil, con la muneca abajo.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_circulo" / "lado"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=olado"

# Perfil (palma al costado) y el aro hacia la camara.
GIROS = [
    (0, 70, 0),
    (0, 90, 0),
    (0, 110, 0),
    (0, -70, 0),
    (0, -90, 0),
    (15, 80, -20),
    (-15, 80, 20),
    (20, 70, -30),
    (10, 100, -15),
    (-10, 60, 25),
    (25, 85, -40),
    (0, 80, -25),
    (30, 75, 10),
    (-20, 95, 15),
    (15, -80, -20),
    (0, 50, -35),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
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
            nombre = f"x{x}_y{y}_z{z}.png"
            viewer.screenshot(path=str(OUT / nombre))
            print(nombre)
        browser.close()


if __name__ == "__main__":
    main()
