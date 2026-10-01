"""J lab 4: palma de lado (LSM) + trazo visible de la J."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j4"

T1 = "mixamorig1RightHandThumb1_036"
ARM = "mixamorig1RightForeArm_034"
FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
    "extra": {T1: {"y": -60, "x": -12}},
}

CASES = {
    "s_y50": {"y": 50},
    "s_y70": {"y": 70},
    "s_y90": {"y": 90},
    "s_y-50": {"y": -50},
    "s_y-70": {"y": -70},
    "s_z90": {"z": 90},
    "s_z-90": {"z": -90},
    "s_y50z15": {"y": 50, "z": 15},
    # trazo desde palma de lado y50
    "y50_x40": {"y": 50, "x": 40},
    "y50_x70": {"y": 50, "x": 70},
    "y50_x-40": {"y": 50, "x": -40},
    "y50_x-70": {"y": 50, "x": -70},
    "y50_z40": {"y": 50, "z": 40},
    "y50_z-40": {"y": 50, "z": -40},
    "y50_z70": {"y": 50, "z": 70},
    "y50_z-70": {"y": 50, "z": -70},
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


def pose(muneca, extra=None):
    data = dict(FINGERS)
    data["muneca"] = muneca
    if extra:
        merged = dict(data["extra"])
        merged.update(extra)
        data["extra"] = merged
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
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            d = m["dir"]
            t = m["tip"]
            print(
                f"{name:12s} tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f}) "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.40m 0.15m';
                    mv.cameraOrbit = '12deg 84deg 2.3m';
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.28m 2.34m 0.18m';
                    mv.cameraOrbit = '8deg 80deg 0.70m';
                    mv.fieldOfView = '22deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))

        browser.close()


if __name__ == "__main__":
    main()
