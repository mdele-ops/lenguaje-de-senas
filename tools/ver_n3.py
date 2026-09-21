"""Encuadra la mano completa para juzgar la N contra la lamina.

Las vistas de `pose_lab_e.set_cam` centran la camara entre muneca y nudillo:
con la muneca caida de la M/N los dedos se salen del cuadro y no se puede ver
cuantas yemas cuelgan. Aqui el objetivo es el centro de TODOS los huesos de la
mano y la camara se aleja lo suficiente para que entren dedos y dorso.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import _GET_SCENE, free_camera
from pose_lab_m5 import hoja
from pose_lab_n3 import CASES, MEASURE_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "ver_n3"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "N_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vern3"

CENTRO_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return null;
  scene.updateMatrixWorld(true);
  const pts = [];
  scene.traverse((o) => {
    if (!o || !o.name || !o.matrixWorld) return;
    if (!/RightHand/.test(o.name)) return;
    const e = o.matrixWorld.elements;
    pts.push({ x: e[12], y: e[13], z: e[14] });
  });
  if (!pts.length) return null;
  const off = (scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
  let min = { x: 1e9, y: 1e9, z: 1e9 }, max = { x: -1e9, y: -1e9, z: -1e9 };
  for (const p of pts) {
    min.x = Math.min(min.x, p.x); max.x = Math.max(max.x, p.x);
    min.y = Math.min(min.y, p.y); max.y = Math.max(max.y, p.y);
    min.z = Math.min(min.z, p.z); max.z = Math.max(max.z, p.z);
  }
  return {
    x: (min.x + max.x) / 2 - off.x,
    y: (min.y + max.y) / 2 - off.y,
    z: (min.z + max.z) / 2 - off.z,
    size: Math.max(max.x - min.x, max.y - min.y, max.z - min.z),
  };
}
"""
)

VISTAS = {
    "dorso": (0, 82),
    "lado": (-60, 82),
    "arriba": (0, 45),
}


def encuadrar(page, c, theta, phi):
    radio = max(0.32, c["size"] * 2.6)
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {
            "t": "%.3fm %.3fm %.3fm" % (c["x"], c["y"], c["z"]),
            "orbit": f"{theta}deg {phi}deg {radio:.3f}m",
            "fov": "26deg",
        },
    )
    time.sleep(0.15)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 760, "height": 760})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        hojas = {k: [("REF foto", REF)] for k in VISTAS}
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.32)
            m = page.evaluate(MEASURE_JS)
            c = page.evaluate(CENTRO_JS)
            print(
                f"{name:14s} down={m['idxDown']:+.2f}/{m['midDown']:+.2f} "
                f"tog={m['togIM']:.2f} ringUp={m['ringUp']:+.2f} size={c['size']:.3f}"
            )
            for vista, (theta, phi) in VISTAS.items():
                encuadrar(page, c, theta, phi)
                ruta = OUT / f"{name}_{vista}.png"
                viewer.screenshot(path=str(ruta))
                hojas[vista].append((name, ruta))

        browser.close()

    for vista, items in hojas.items():
        hoja(items, OUT / f"_{vista}.png", cols=4, cell=300)


if __name__ == "__main__":
    main()
