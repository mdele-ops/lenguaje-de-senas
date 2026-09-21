"""Verifica la Ñ: el barrido lateral por el camino real de la app."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "enie_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=enie3"

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
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  function pos(name) {
    const b = bones[name];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const dx = i4.x - i1.x, dy = i4.y - i1.y, dz = i4.z - i1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return { tip: i4, dir: { x: dx / len, y: dy / len, z: dz / len } };
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
        time.sleep(0.8)

        viewer = page.query_selector("#viewer")
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '0m 2.45m 0.15m';
                mv.cameraOrbit = '0deg 84deg 2.5m';
                mv.fieldOfView = '30deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.3)

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('Ñ')")
        # Deja pasar la transicion de 2 s y el hold inicial.
        time.sleep(2.6)

        xs, ys, zs = [], [], []
        for i in range(60):
            m = page.evaluate(MEASURE_JS)
            t, d = m["tip"], m["dir"]
            xs.append(t["x"])
            ys.append(t["y"])
            zs.append(t["z"])
            print(
                f"t={i * 100:4d}ms  tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f})  "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            if i % 4 == 0:
                viewer.screenshot(path=str(OUT_DIR / f"ciclo_{i:02d}.png"))
            time.sleep(0.1)

        print(
            f"lateral  x min={min(xs):+.3f} max={max(xs):+.3f} recorrido={(max(xs) - min(xs)) * 100:.1f} cm"
        )
        print(
            f"vertical y min={min(ys):+.3f} max={max(ys):+.3f} deriva={(max(ys) - min(ys)) * 100:.1f} cm"
        )
        print(
            f"fondo    z min={min(zs):+.3f} max={max(zs):+.3f} deriva={(max(zs) - min(zs)) * 100:.1f} cm"
        )

        browser.close()


if __name__ == "__main__":
    main()
