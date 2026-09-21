"""J lab 10: trazo con asta vertical y gancho que sube (J legible)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j10"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j10"

T1 = "mixamorig1RightHandThumb1_036"
FORE = "mixamorig1RightForeArm_034"
THUMB = {T1: {"y": -60, "x": -12}}
FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
}

MEASURE_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(mv) {
    if (mv.model && typeof mv.model.traverse === 'function') return mv.model;
    if (mv.model && mv.model.scene && typeof mv.model.scene.traverse === 'function') return mv.model.scene;
    const symbols = Object.getOwnPropertySymbols(mv);
    for (let i = 0; i < symbols.length; i++) {
      const value = mv[symbols[i]];
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
  const dx = p4.x - p1.x, dy = p4.y - p1.y, dz = p4.z - p1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return { tip: p4, dir: { x: dx / len, y: dy / len, z: dz / len } };
}
"""


def pose(muneca, fx=0):
    extra = dict(THUMB)
    extra[FORE] = {"x": fx}
    data = dict(FINGERS)
    data["muneca"] = muneca
    data["extra"] = extra
    return data


SEQ = {
    "g0": pose({"x": 0, "y": 0, "z": 0}, 0),
    "g1": pose({"x": 4, "y": 0, "z": 6}, 20),
    "g2": pose({"x": 8, "y": 0, "z": 12}, 38),
    "g3": pose({"x": 16, "y": -4, "z": 48}, 36),
    "g4": pose({"x": 8, "y": -12, "z": 82}, 24),
    "g5": pose({"x": -8, "y": -18, "z": 70}, 8),
    "h0": pose({"x": 0, "y": 0, "z": 0}, 0),
    "h1": pose({"x": 5, "y": 0, "z": 8}, 22),
    "h2": pose({"x": 10, "y": 0, "z": 14}, 40),
    "h3": pose({"x": 18, "y": 6, "z": -50}, 34),
    "h4": pose({"x": 10, "y": 14, "z": -85}, 22),
    "h5": pose({"x": -6, "y": 22, "z": -70}, 6),
}


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
        page.evaluate(
            "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", SEQ["g0"]
        )
        time.sleep(0.4)

        viewer = page.query_selector("#viewer")
        for name, data in SEQ.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.18)
            m = page.evaluate(MEASURE_JS)
            t = m["tip"]
            d = m["dir"]
            print(
                f"{name}  tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f}) "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.38m 0.15m';
                    mv.cameraOrbit = '10deg 84deg 2.15m';
                    mv.fieldOfView = '28deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.1)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))

        browser.close()


if __name__ == "__main__":
    main()
