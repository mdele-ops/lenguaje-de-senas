"""I lab 4: pulgar estilo B mas apretado contra los dedos cerrados."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_i4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=i4"

T1 = "mixamorig1RightHandThumb1_036"

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
  function dist(a, b) {
    if (!a || !b) return null;
    return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
  }
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i2 = pos('mixamorig1RightHandIndex2_041');
  const i3 = pos('mixamorig1RightHandIndex3_042');
  const m2 = pos('mixamorig1RightHandMiddle2_045');
  return {
    dIndex2: dist(t4, i2),
    dIndex3: dist(t4, i3),
    dMiddle2: dist(t4, m2),
  };
}
"""


def pose(thumb, extra=None):
    data = {
        "thumb": thumb,
        "index": {"curl": 0.95},
        "middle": {"curl": 0.95},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.0},
    }
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_current": pose({"curl": 0.6}),
    "01_b60": pose({"curl": 0.74, "aside": -0.5}, extra={T1: {"y": -60}}),
    "02_b70": pose({"curl": 0.74, "aside": -0.5}, extra={T1: {"y": -70}}),
    "03_b80": pose({"curl": 0.74, "aside": -0.5}, extra={T1: {"y": -80}}),
    "04_b60_x12": pose(
        {"curl": 0.74, "aside": -0.5}, extra={T1: {"y": -60, "x": -12}}
    ),
    "05_b70_x12": pose(
        {"curl": 0.78, "aside": -0.55}, extra={T1: {"y": -70, "x": -12}}
    ),
    "06_y55_aside06": pose(
        {"curl": 0.7, "aside": -0.6}, extra={T1: {"y": -55}}
    ),
    "07_y65_curl08": pose(
        {"curl": 0.82, "aside": -0.5}, extra={T1: {"y": -65}}
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
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.22)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name}: i2={m['dIndex2']:.4f} i3={m['dIndex3']:.4f} "
                f"m2={m['dMiddle2']:.4f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.3m 2.3m 0.15m';
                    mv.cameraOrbit = '5deg 82deg 0.75m';
                    mv.fieldOfView = '25deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_rev.png"))
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

        browser.close()


if __name__ == "__main__":
    main()
