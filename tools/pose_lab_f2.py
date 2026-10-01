"""Afina F: cierra yemas pulgar-indice a partir de 05_d_soft."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f2"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"
I1 = "mixamorig1RightHandIndex1_040"
I2 = "mixamorig1RightHandIndex2_041"
I3 = "mixamorig1RightHandIndex3_042"

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
  const index = pos('mixamorig1RightHandIndex4_043');
  if (!thumb || !index) return { error: 'bones' };
  const dx = thumb.x - index.x;
  const dy = thumb.y - index.y;
  const dz = thumb.z - index.z;
  return { dist: Math.sqrt(dx*dx+dy*dy+dz*dz), dx, dy, dz };
}
"""


def pose(t_curl, aside, i_curl, extra=None, i_spread=0):
    data = {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": i_curl, "spread": i_spread} if i_spread else {"curl": i_curl},
        "middle": {"curl": 0.0},
        "ring": {"curl": 0.0},
        "pinky": {"curl": 0.0},
    }
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_soft": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}}),
    "01_z28": pose(0.50, 0.30, 0.52, {T1: {"z": 28, "y": -4}, T2: {"x": -20}}),
    "02_z34": pose(0.50, 0.30, 0.52, {T1: {"z": 34, "y": -4}, T2: {"x": -20}}),
    "03_x-28": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -28}}),
    "04_x-36": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}),
    "05_curl58": pose(0.50, 0.30, 0.58, {T1: {"z": 22, "y": -4}, T2: {"x": -20}}),
    "06_curl64": pose(0.50, 0.30, 0.64, {T1: {"z": 22, "y": -4}, T2: {"x": -20}}),
    "07_tcurl56": pose(0.56, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}}),
    "08_aside40": pose(0.50, 0.40, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}}),
    "09_aside50": pose(0.50, 0.50, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}}),
    "10_y-12": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -12}, T2: {"x": -20}}),
    "11_y8": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": 8}, T2: {"x": -20}}),
    "12_i1x12": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}, I1: {"x": 12}}),
    "13_i2x16": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}, I2: {"x": 16}}),
    "14_i3x20": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}, I3: {"x": 20}}),
    "15_combo": pose(
        0.52,
        0.38,
        0.58,
        {T1: {"z": 30, "y": -6}, T2: {"x": -28}, I2: {"x": 10}},
    ),
    "16_combo2": pose(
        0.54,
        0.42,
        0.60,
        {T1: {"z": 34, "y": -8}, T2: {"x": -32}, I3: {"x": 14}},
    ),
    "17_d_on_index": pose(
        0.54,
        0.38,
        0.56,
        {T1: {"z": 38, "y": -5}, T2: {"x": -37}},
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
            time.sleep(0.16)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m["dist"], m))
            print(
                f"{name}: dist={m['dist']:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))
            cam("-0.30m 2.36m 0.20m", "12deg 76deg 0.42m", "16deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_tips.png"))

        print("closest:")
        for name, dist, m in sorted(ranked, key=lambda x: x[1])[:8]:
            print(
                f"  {name}: {dist:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
