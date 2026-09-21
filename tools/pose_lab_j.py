"""J lab 1: medir ejes de muneca sobre la pose I (menique arriba)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j1"

T1 = "mixamorig1RightHandThumb1_036"

I_FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
    "extra": {T1: {"y": -60, "x": -12}},
}

CASES = {
    "00_I": {},
    "x-40": {"x": -40},
    "x40": {"x": 40},
    "x-70": {"x": -70},
    "x70": {"x": 70},
    "y-40": {"y": -40},
    "y40": {"y": 40},
    "y-70": {"y": -70},
    "y70": {"y": 70},
    "z-40": {"z": -40},
    "z40": {"z": 40},
    "z-70": {"z": -70},
    "z70": {"z": 70},
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
  const hand = pos('mixamorig1RightHand_035');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  if (!p1 || !p4) return { error: 'bones' };
  const dx = p4.x - p1.x, dy = p4.y - p1.y, dz = p4.z - p1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return {
    pinky: p4,
    base: p1,
    hand: hand,
    thumb: t4,
    dir: { x: dx / len, y: dy / len, z: dz / len },
  };
}
"""


def pose_with(muneca):
    data = dict(I_FINGERS)
    if muneca:
        data = dict(data)
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
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose_with(muneca),
            )
            time.sleep(0.22)
            m = page.evaluate(MEASURE_JS)
            p = m["pinky"]
            d = m["dir"]
            print(
                f"{name:8s}  tip=({p['x']:+.3f},{p['y']:+.3f},{p['z']:+.3f})  "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '-40deg 80deg 0.55m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_user.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.3m 2.3m 0.15m';
                    mv.cameraOrbit = '5deg 82deg 0.75m';
                    mv.fieldOfView = '25deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_rev.png"))

        browser.close()


if __name__ == "__main__":
    main()
