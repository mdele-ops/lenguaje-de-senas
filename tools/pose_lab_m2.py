"""M lab 2: colgar la muneca para que los tres dedos apunten al piso."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_m2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=m2"

T1 = "mixamorig1RightHandThumb1_036"
ARM = "mixamorig1RightArm_033"

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
  const index = dir(i1, i4);
  return { idxDown: index.y, idxFwd: index.z, idxX: index.x, tip: i4 };
}
"""


def pose(muneca=None, extra=None):
    data = {
        "thumb": {"curl": 0.74, "aside": -0.5},
        "index": {"curl": 0.05, "spread": 8},
        "middle": {"curl": 0.05},
        "ring": {"curl": 0.05, "spread": -8},
        "pinky": {"curl": 0.95},
        "extra": {T1: {"y": -60, "x": -12}},
    }
    if muneca:
        data["muneca"] = muneca
    if extra:
        data["extra"].update(extra)
    return data


CASES = {
    "00_up": pose(),
    "01_x120": pose({"x": 120}),
    "02_x140": pose({"x": 140}),
    "03_x160": pose({"x": 160}),
    "04_x175": pose({"x": 175}),
    "05_x140_arm": pose({"x": 140}, extra={ARM: {"z": -18}}),
    "06_x160_arm": pose({"x": 160}, extra={ARM: {"z": -18}}),
    "07_y180_x40": pose({"y": 180, "x": 40}),
    "08_y180_x80": pose({"y": 180, "x": 80}),
    "09_y180_x120": pose({"y": 180, "x": 120}),
    "10_x150_y15": pose({"x": 150, "y": 15}),
    "11_x150_z-15": pose({"x": 150, "z": -15}),
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
        time.sleep(1.2)

        viewer = page.query_selector("#viewer")
        page.evaluate(
            "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
            pose(),
        )
        time.sleep(0.5)

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.22)
            m = page.evaluate(MEASURE_JS)
            if not m or m.get("error"):
                print(f"{name:14s}  ERROR {m}")
                continue
            print(
                f"{name:14s}  down={m['idxDown']:+.3f} fwd={m['idxFwd']:+.3f} "
                f"x={m['idxX']:+.3f}  tip=({m['tip']['x']:+.3f},{m['tip']['y']:+.3f},{m['tip']['z']:+.3f})"
            )

            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.18m 2.18m 0.18m';
                    mv.cameraOrbit = '22deg 78deg 1.15m';
                    mv.fieldOfView = '22deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_wide.png"))

            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.22m 2.12m 0.22m';
                    mv.cameraOrbit = '-8deg 80deg 0.85m';
                    mv.fieldOfView = '20deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.10)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        browser.close()


if __name__ == "__main__":
    main()
