"""Letra F: indice y pulgar forman circulo; medio, anular y menique arriba."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f1"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I1 = "mixamorig1RightHandIndex1_040"

MEASURE_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(modelViewer) {
    if (modelViewer.model && typeof modelViewer.model.traverse === 'function') return modelViewer.model;
    if (modelViewer.model && modelViewer.model.scene && typeof modelViewer.model.traverse === 'function') return modelViewer.model.scene;
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
  const index = pos('mixamorig1RightHandIndex4_043');
  if (!thumb || !index) return { error: 'bones', thumb, index };
  const dx = thumb.x - index.x;
  const dy = thumb.y - index.y;
  const dz = thumb.z - index.z;
  return {
    dist: Math.sqrt(dx * dx + dy * dy + dz * dz),
    dx, dy, dz, thumb, index
  };
}
"""


def pose(thumb, index, extra=None, spread_up=None):
    data = {
        "thumb": thumb,
        "index": index if isinstance(index, dict) else {"curl": index},
        "middle": {"curl": 0.0},
        "ring": {"curl": 0.0},
        "pinky": {"curl": 0.0},
    }
    if spread_up:
        data["middle"]["spread"] = spread_up[0]
        data["ring"]["spread"] = spread_up[1]
        data["pinky"]["spread"] = spread_up[2]
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_actual": pose({"curl": 0.65}, {"curl": 0.95}),
    "01_o_like": pose({"curl": 0.55, "aside": 0.30}, {"curl": 0.60}),
    "02_o_open": pose({"curl": 0.50, "aside": 0.32}, {"curl": 0.52}),
    "03_o_tight": pose({"curl": 0.58, "aside": 0.36}, {"curl": 0.58}),
    "04_d_thumb": pose(
        {"curl": 0.54, "aside": 0.38},
        {"curl": 0.56},
        extra={T1: {"z": 38, "y": -5}, T2: {"x": -37}},
    ),
    "05_d_soft": pose(
        {"curl": 0.50, "aside": 0.30},
        {"curl": 0.52},
        extra={T1: {"z": 22, "y": -4}, T2: {"x": -20}},
    ),
    "06_thumb_z30": pose(
        {"curl": 0.52, "aside": 0.34},
        {"curl": 0.54},
        extra={T1: {"z": 30}},
    ),
    "07_thumb_z-20": pose(
        {"curl": 0.52, "aside": 0.34},
        {"curl": 0.54},
        extra={T1: {"z": -20}},
    ),
    "08_thumb_y20": pose(
        {"curl": 0.52, "aside": 0.34},
        {"curl": 0.54},
        extra={T1: {"y": 20}},
    ),
    "09_thumb_y-20": pose(
        {"curl": 0.52, "aside": 0.34},
        {"curl": 0.54},
        extra={T1: {"y": -20}},
    ),
    "10_t2x-25": pose(
        {"curl": 0.54, "aside": 0.36},
        {"curl": 0.56},
        extra={T2: {"x": -25}},
    ),
    "11_idx_spread": pose(
        {"curl": 0.52, "aside": 0.36},
        {"curl": 0.54, "spread": 8},
    ),
    "12_idx_spread_neg": pose(
        {"curl": 0.52, "aside": 0.36},
        {"curl": 0.54, "spread": -8},
    ),
    "13_combo": pose(
        {"curl": 0.54, "aside": 0.36},
        {"curl": 0.56, "spread": 6},
        extra={T1: {"z": 24, "y": 8}, T2: {"x": -18}},
    ),
    "14_circle_soft": pose(
        {"curl": 0.48, "aside": 0.40},
        {"curl": 0.48},
        extra={T1: {"y": 12}},
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
        print("closest thumb-index:")
        for name, dist in ranked[:8]:
            print(f"  {name}: {dist:.4f}")

        browser.close()


if __name__ == "__main__":
    main()
