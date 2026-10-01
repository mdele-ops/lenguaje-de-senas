"""Verifica la letra M desde el boton real de practica.html."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera, set_cam
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_m_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=M&v=mvolando"

MEASURE_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(modelViewer) {
    if (modelViewer.model && typeof modelViewer.model.traverse === 'function') return modelViewer.model;
    if (modelViewer.model && modelViewer.model.scene && typeof modelViewer.model.scene.traverse === 'function') return modelViewer.model.scene;
    const symbols = Object.getOwnPropertySymbols(modelViewer);
    for (let i = 0; i < symbols.length; i++) {
      const value = modelViewer[symbols[i]];
      if (value && typeof value.traverse === 'function') return value;
      if (value && value.model && typeof value.model.traverse === 'function') return value.model;
      if (value && value.target && typeof value.target.traverse === 'function') return value.target;
    }
    return null;
  }
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  function pos(name) {
    const b = bones[name];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  function dir(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    const len = Math.hypot(dx, dy, dz) || 1;
    return { x: dx / len, y: dy / len, z: dz / len };
  }
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const index = dir(i1, i4);
  return {
    idxDown: index.y,
    togIM: Math.hypot(i4.x - m4.x, i4.y - m4.y, i4.z - m4.z),
    togMR: Math.hypot(m4.x - r4.x, m4.y - r4.y, m4.z - r4.z),
    pinkyBelowIndex: p4.y < i4.y,
    caption: document.getElementById('anim-info') && document.getElementById('anim-info').textContent,
    letter: document.getElementById('current-letter') && document.getElementById('current-letter').textContent,
  };
}
"""


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.4)

        result = page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('M')")
        print("mostrarSena:", result)
        time.sleep(2.6)

        m = page.evaluate(MEASURE_JS)
        print("measure M:", m)
        print(
            "caption:",
            page.evaluate(
                "() => document.getElementById('anim-info') && document.getElementById('anim-info').textContent"
            ),
        )

        viewer = page.query_selector("#viewer")
        viewer.screenshot(path=str(OUT_DIR / "M_produccion.png"))

        free_camera(page)
        hand = page.evaluate(HAND_POS_JS)
        set_cam(page, "prod", hand)
        time.sleep(0.35)
        viewer.screenshot(path=str(OUT_DIR / "M_cuerpo.png"))
        set_cam(page, "mano", hand)
        time.sleep(0.2)
        viewer.screenshot(path=str(OUT_DIR / "M_mano.png"))
        set_cam(page, "lado", hand)
        time.sleep(0.2)
        viewer.screenshot(path=str(OUT_DIR / "M_lado.png"))

        browser.close()


if __name__ == "__main__":
    main()
