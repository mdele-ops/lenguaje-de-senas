"""Letra D: indice arriba, pulgar y medio se juntan en circulo."""
import math
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_d"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=d1"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
M1 = "mixamorig1RightHandMiddle1_044"
M2 = "mixamorig1RightHandMiddle2_045"

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
  const thumb = pos('mixamorig1RightHandThumb4_039');
  const middle = pos('mixamorig1RightHandMiddle4_047');
  const index = pos('mixamorig1RightHandIndex4_043');
  if (!thumb || !middle) return { error: 'bones', thumb, middle };
  const dx = thumb.x - middle.x;
  const dy = thumb.y - middle.y;
  const dz = thumb.z - middle.z;
  return {
    dist: Math.sqrt(dx * dx + dy * dy + dz * dz),
    thumb, middle, index
  };
}
"""


def pose(thumb, middle, ring=0.92, pinky=0.92, extra=None, muneca=None):
    data = {
        "thumb": thumb,
        "index": {"curl": 0.0},
        "middle": middle if isinstance(middle, dict) else {"curl": middle},
        "ring": {"curl": ring},
        "pinky": {"curl": pinky},
    }
    if extra:
        data["extra"] = extra
    if muneca:
        data["muneca"] = muneca
    return data


CASES = {
    "00_actual": pose({"curl": 0.55, "aside": 0.1}, {"curl": 0.95}),
    "01_o_middle": pose({"curl": 0.55, "aside": 0.35}, {"curl": 0.58}),
    "02_o_group": pose(
        {"curl": 0.55, "aside": 0.32},
        {"curl": 0.58},
        ring=0.62,
        pinky=0.64,
    ),
    "03_tight": pose({"curl": 0.62, "aside": 0.42}, {"curl": 0.64}),
    "04_open": pose({"curl": 0.48, "aside": 0.40}, {"curl": 0.50}),
    "05_thumb_y20": pose(
        {"curl": 0.55, "aside": 0.38},
        {"curl": 0.56},
        extra={T1: {"y": 20}},
    ),
    "06_thumb_y-20": pose(
        {"curl": 0.55, "aside": 0.38},
        {"curl": 0.56},
        extra={T1: {"y": -20}},
    ),
    "07_thumb_z30": pose(
        {"curl": 0.52, "aside": 0.36},
        {"curl": 0.56},
        extra={T1: {"z": 30}},
    ),
    "08_thumb_z-30": pose(
        {"curl": 0.52, "aside": 0.36},
        {"curl": 0.56},
        extra={T1: {"z": -30}},
    ),
    "09_t2x-25": pose(
        {"curl": 0.58, "aside": 0.40},
        {"curl": 0.60},
        extra={T2: {"x": -25}},
    ),
    "10_mid_spread": pose(
        {"curl": 0.55, "aside": 0.38},
        {"curl": 0.56, "spread": -12},
    ),
    "11_combo": pose(
        {"curl": 0.58, "aside": 0.42},
        {"curl": 0.58, "spread": -8},
        extra={T1: {"y": 16}, M1: {"x": 8}},
    ),
    "12_circle_like_o": pose(
        {"curl": 0.55, "aside": 0.30},
        {"curl": 0.60},
        ring=0.88,
        pinky=0.90,
        extra={T1: {"y": 18}},
    ),
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
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")

        def cam(target, orbit, fov):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.2)

        results = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.25)
            measure = page.evaluate(MEASURE_JS)
            dist = measure.get("dist") if isinstance(measure, dict) else None
            results.append((name, dist, measure))
            print(f"{name}: dist={dist}")

            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        ranked = sorted(
            [(n, d) for n, d, _ in results if isinstance(d, (int, float))],
            key=lambda x: x[1],
        )
        print("closest thumb-middle:")
        for name, dist in ranked[:6]:
            print(f"  {name}: {dist:.4f}")

        browser.close()


if __name__ == "__main__":
    main()
