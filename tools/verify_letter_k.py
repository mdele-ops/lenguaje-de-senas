"""Verifica la letra K: extremos del vaiven y serie temporal de profundidad."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_k_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=k2"

K_FINGERS = {
    "thumb": {"curl": 0.25, "aside": 0.2},
    "index": {"curl": 0.0},
    "middle": {"curl": 0.4},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.95},
}

POSES = {
    "frente": {**K_FINGERS, "muneca": {"x": 30, "y": 0, "z": 0}},
    "centro": {**K_FINGERS, "muneca": {"x": 0, "y": 0, "z": 0}},
    "atras": {**K_FINGERS, "muneca": {"x": -24, "y": 0, "z": 0}},
}

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
  return { tip: pos('mixamorig1RightHandIndex4_043') };
}
"""


def set_cam(page, orbit):
    page.evaluate(
        """(orbit) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = '0m 2.40m 0.15m';
            mv.cameraOrbit = orbit;
            mv.fieldOfView = '30deg';
            mv.jumpCameraToGoal();
        }""",
        orbit,
    )


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

        for name, pose in POSES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", pose
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            t = m["tip"]
            print(f"{name:8s}  tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f})")
            set_cam(page, "8deg 84deg 2.3m")
            time.sleep(0.08)
            viewer.screenshot(path=str(OUT_DIR / f"pose_{name}_front.png"))
            set_cam(page, "42deg 84deg 2.3m")
            time.sleep(0.08)
            viewer.screenshot(path=str(OUT_DIR / f"pose_{name}_side.png"))

        set_cam(page, "42deg 84deg 2.3m")
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('K')")
        time.sleep(2.2)
        zs = []
        xs = []
        for i in range(60):
            m = page.evaluate(MEASURE_JS)
            zs.append(m["tip"]["z"])
            xs.append(m["tip"]["x"])
            print(f"t={i * 100:4d}ms  z={m['tip']['z']:+.3f}  x={m['tip']['x']:+.3f}")
            if i % 6 == 0:
                viewer.screenshot(path=str(OUT_DIR / f"ciclo_{i:02d}.png"))
            time.sleep(0.1)
        print(f"z min={min(zs):+.3f}  max={max(zs):+.3f}  range={max(zs) - min(zs):.3f}")
        print(f"x min={min(xs):+.3f}  max={max(xs):+.3f}  range={max(xs) - min(xs):.3f}")

        browser.close()


if __name__ == "__main__":
    main()
