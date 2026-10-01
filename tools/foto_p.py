"""Retrata la P (pose del catalogo o de un json) cerca de la mano, en varias vistas."""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "foto_p"
OUT.mkdir(parents=True, exist_ok=True)
se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=fotop"

MANO_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(mv) {
    if (mv.model && typeof mv.model.traverse === 'function') return mv.model;
    if (mv.model && mv.model.scene) return mv.model.scene;
    for (const s of Object.getOwnPropertySymbols(mv)) {
      const v = mv[s];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
    }
    return null;
  }
  const sc = getScene(mv);
  sc.updateMatrixWorld(true);
  let t = null;
  sc.traverse((o) => { if (o.name && /RightHandThumb4/.test(o.name)) t = o; });
  const e = t.matrixWorld.elements;
  const off = (sc.target && sc.target.position) || { x: 0, y: 0, z: 0 };
  return { x: e[12] - off.x, y: e[13] - off.y, z: e[14] - off.z };
}
"""

VISTAS = {
    "frente": "0deg 84deg 0.16m",
    "perfil": "-70deg 84deg 0.16m",
    "perfil2": "70deg 84deg 0.16m",
    "abajo": "0deg 130deg 0.16m",
    "arriba": "0deg 40deg 0.16m",
}


def main():
    pose = None
    if len(sys.argv) > 1:
        pose = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    etiqueta = sys.argv[2] if len(sys.argv) > 2 else "p"
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 700})
        time.sleep(0.5)
        if pose is None:
            page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('P')")
            time.sleep(2.6)
        else:
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.8)
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.minCameraOrbit = 'auto 0deg 0.05m';
                mv.maxCameraOrbit = 'auto 180deg 10m';
                mv.minFieldOfView = '2deg';
            }"""
        )
        m = page.evaluate(MANO_JS)
        t = "%.4fm %.4fm %.4fm" % (m["x"], m["y"], m["z"])
        viewer = page.query_selector("#viewer")
        for nombre, orbit in VISTAS.items():
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t; mv.cameraOrbit = a.o;
                    mv.fieldOfView = '20deg'; mv.jumpCameraToGoal();
                }""",
                {"t": t, "o": orbit},
            )
            time.sleep(0.6)
            viewer.screenshot(path=str(OUT / f"{etiqueta}_{nombre}.png"))
        browser.close()
    print("fotos en", OUT)


if __name__ == "__main__":
    main()

