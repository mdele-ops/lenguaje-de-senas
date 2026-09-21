"""Verifica la letra O desde el boton real de practica.html."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_o_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?letra=O&v=ofinal1"

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
  function dist(a, b) {
    if (!a || !b) return null;
    return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
  }
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  return {
    dI: dist(t4, i4),
    dM: dist(t4, m4),
    dR: dist(t4, r4),
    dP: dist(t4, p4),
    caption: document.getElementById('anim-info') && document.getElementById('anim-info').textContent,
    letter: document.getElementById('current-letter') && document.getElementById('current-letter').textContent,
  };
}
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        time.sleep(8)
        ready = False
        for _ in range(80):
            try:
                if page.evaluate(
                    "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
                ):
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.3)
        if not ready:
            raise RuntimeError("El modelo 3D no cargo a tiempo")
        time.sleep(1.0)

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('O')")
        time.sleep(2.4)

        m = page.evaluate(MEASURE_JS)
        print("measure O:", str(m).encode("ascii", "replace").decode("ascii"))

        viewer = page.query_selector("#viewer")
        viewer.screenshot(path=str(OUT_DIR / "O_produccion.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '0m 2.40m 0.15m';
                mv.cameraOrbit = '28deg 84deg 2.4m';
                mv.fieldOfView = '30deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "O_cuerpo.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '8deg 78deg 0.50m';
                mv.fieldOfView = '18deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "O_perfil.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '-55deg 80deg 0.55m';
                mv.fieldOfView = '20deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "O_palma.png"))

        pose = page.evaluate(
            """() => {
                const s = window.__LSM_CONTROLLER__.getSena('O');
                return s && s.pose;
            }"""
        )
        print("pose O:", pose)
        browser.close()


if __name__ == "__main__":
    main()
