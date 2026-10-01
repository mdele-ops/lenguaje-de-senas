"""Gira la muneca de la O hasta que el agujero mire a la camara, como la foto."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9
from o_circulo import MEDIR_JS, linea, pose, puntuar

search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=ogiro"
OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "o_circulo" / "giro"

BASE = dict(icurl=0.68, i1=32, i2=8, i3=-8, ispread=6,
            tcurl=0.30, aside=-0.3, t1x=-10, t1y=-30, t1z=65, t2x=55, t3x=55)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    casos = []
    for y in (-150, -110, -70, -30, 0, 40, 80, 120, 160):
        casos.append((f"y{y}", pose(muneca={"y": y}, cerrar=1.0, **BASE)))
    for x in (-50, -25, 25, 50):
        casos.append((f"x{x}", pose(muneca={"x": x}, cerrar=1.0, **BASE)))
    for z in (-60, -30, 30, 60):
        casos.append((f"z{z}", pose(muneca={"z": z}, cerrar=1.0, **BASE)))
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_viewport_size({"width": 640, "height": 640})
        viewer = page.query_selector("#handViewer")
        for nombre, pz in casos:
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.15)
            m = page.evaluate(MEDIR_JS, pz)
            print(linea(nombre, m, puntuar(m)))
            h = page.evaluate(
                """() => {
                  const mv = document.getElementById('handViewer');
                  let s = null;
                  for (const sym of Object.getOwnPropertySymbols(mv)) {
                    const v = mv[sym];
                    if (v && typeof v.traverse === 'function') { s = v; break; }
                  }
                  s.updateMatrixWorld(true);
                  const B = {};
                  s.traverse((o) => { if (o && o.name) B[o.name] = o; });
                  const e = B.RightHandIndex2.matrixWorld.elements;
                  const off = (s.target && s.target.position) || {x:0,y:0,z:0};
                  return { x: e[12]-off.x, y: e[13]-off.y, z: e[14]-off.z };
                }"""
            )
            t = "%.3fm %.3fm %.3fm" % (h["x"], h["y"], h["z"])
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.minCameraOrbit = 'auto 0deg 0.05m';
                    mv.maxCameraOrbit = 'auto 180deg 10m';
                    mv.cameraTarget = a.t;
                    mv.cameraOrbit = '8deg 70deg 0.34m';
                    mv.fieldOfView = '20deg';
                    mv.jumpCameraToGoal();
                }""",
                {"t": t},
            )
            time.sleep(0.25)
            viewer.screenshot(path=str(OUT / f"{nombre}.png"))
            (OUT / f"{nombre}.json").write_text(json.dumps(pz), encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
