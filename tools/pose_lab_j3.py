"""J lab 3: trazo hacia el pulgar (z negativo) + flexion de muneca (x positivo)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j3"

T1 = "mixamorig1RightHandThumb1_036"
FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
    "extra": {T1: {"y": -60, "x": -12}},
}

CASES = {
    "00_start": {"x": 0, "y": 0, "z": 0},
    "01_down": {"x": 38, "y": 0, "z": -8},
    "02_mid": {"x": 50, "y": -8, "z": -22},
    "03_bottom": {"x": 48, "y": -18, "z": -42},
    "04_hook": {"x": 22, "y": -28, "z": -62},
    "05_hook2": {"x": 12, "y": -35, "z": -72},
    "06_hook3": {"x": 28, "y": -40, "z": -55},
    "07_sweep": {"x": 45, "y": -50, "z": -35},
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
  const p1 = pos('mixamorig1RightHandPinky1_052');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  if (!p1 || !p4) return { error: 'bones' };
  const dx = p4.x - p1.x, dy = p4.y - p1.y, dz = p4.z - p1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return { tip: p4, dir: { x: dx / len, y: dy / len, z: dz / len } };
}
"""


def pose(muneca):
    data = dict(FINGERS)
    data["muneca"] = muneca
    return data


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        time.sleep(7)
        for _ in range(50):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")
        for name, muneca in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", pose(muneca)
            )
            time.sleep(0.22)
            m = page.evaluate(MEASURE_JS)
            t = m["tip"]
            d = m["dir"]
            print(
                f"{name:10s} tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f}) "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            for cam, js in [
                (
                    "user",
                    """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '-40deg 80deg 0.55m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }""",
                ),
                (
                    "rev",
                    """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.3m 2.3m 0.15m';
                    mv.cameraOrbit = '5deg 82deg 0.75m';
                    mv.fieldOfView = '25deg';
                    mv.jumpCameraToGoal();
                }""",
                ),
                (
                    "body",
                    """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.40m 0.15m';
                    mv.cameraOrbit = '18deg 84deg 2.4m';
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }""",
                ),
            ]:
                page.evaluate(js)
                time.sleep(0.12)
                viewer.screenshot(path=str(OUT_DIR / f"{name}_{cam}.png"))

        browser.close()


if __name__ == "__main__":
    main()
