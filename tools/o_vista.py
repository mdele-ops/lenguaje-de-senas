"""Misma forma de O, girando la muneca hasta que el aro mire a la camara de la pagina."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9
from o_circulo import pose

search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=ovista"
OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "o_circulo" / "vista"

BASE = dict(
    icurl=0.64, i1=24, i2=6, i3=-10, ispread=4,
    tcurl=0.22, aside=-0.3, t1x=-8, t1y=-28, t1z=40, t2x=35, t3x=80,
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    casos = []
    for y in range(-160, 30, 20):
        casos.append((f"y{y}", {"y": y}))
    for z in (-80, -40, 40, 80):
        casos.append((f"z{z}", {"z": z}))
    for x in (-40, 40):
        casos.append((f"x{x}", {"x": x}))
    # combinaciones alrededor del perfil que ya cierra
    for y, z in ((-70, -40), (-70, 40), (-20, -50), (20, -40), (-110, 30)):
        casos.append((f"y{y}z{z}", {"y": y, "z": z}))

    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_viewport_size({"width": 720, "height": 720})
        viewer = page.query_selector("#handViewer")
        for nombre, muneca in casos:
            pz = pose(muneca=muneca, cerrar=1.0, **BASE)
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.2)
            page.evaluate(
                """() => {
                  const mv = document.getElementById('handViewer');
                  mv.minCameraOrbit = 'auto 0deg 0.05m';
                  mv.maxCameraOrbit = 'auto 180deg 10m';
                  const orb = mv.getCameraOrbit();
                  mv.cameraOrbit = orb.theta + 'rad ' + orb.phi + 'rad 0.32m';
                  mv.fieldOfView = '26deg';
                  mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.28)
            viewer.screenshot(path=str(OUT / f"{nombre}.png"))
            print(nombre)
        browser.close()


if __name__ == "__main__":
    main()
