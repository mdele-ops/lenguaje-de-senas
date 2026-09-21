"""Verifica la letra N desde el boton real de practica.html."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_n_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 127.0.0.1 y no localhost: el servidor de pruebas escucha en IPv4 y Chrome
# resuelve localhost por IPv6 (::1), lo que devuelve ERR_EMPTY_RESPONSE.
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=nfinal3"

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
    ringHigher: r4.y > i4.y,
    pinkyHigher: p4.y > i4.y,
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
        page.goto(URL, wait_until="domcontentloaded")
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

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('N')")
        time.sleep(2.4)

        m = page.evaluate(MEASURE_JS)
        print("measure N:", str(m).encode("ascii", "replace").decode("ascii"))

        viewer = page.query_selector("#viewer")
        viewer.screenshot(path=str(OUT_DIR / "N_produccion.png"))

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
        viewer.screenshot(path=str(OUT_DIR / "N_cuerpo.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.18m 2.20m 0.18m';
                mv.cameraOrbit = '22deg 78deg 1.15m';
                mv.fieldOfView = '22deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "N_mano.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.22m 2.14m 0.22m';
                mv.cameraOrbit = '-6deg 80deg 0.80m';
                mv.fieldOfView = '20deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "N_frente.png"))

        browser.close()


if __name__ == "__main__":
    main()
