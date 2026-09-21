"""H lab 2: dorso al frente, dedos a la derecha, pulgar arriba."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_h2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=h2"

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
    return { x: +e[12].toFixed(3), y: +e[13].toFixed(3), z: +e[14].toFixed(3) };
  }
  function dir(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    const len = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1;
    return { up: +(dy/len).toFixed(3), x: +(dx/len).toFixed(3), z: +(dz/len).toFixed(3) };
  }
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const hand = pos('mixamorig1RightHand_035');
  if (!t1 || !t4 || !i1 || !i4) return { error: 'bones' };
  return {
    hand, i4, t4,
    thumb: dir(t1, t4),
    index: dir(i1, i4),
    together: +Math.hypot(i4.x-m4.x, i4.y-m4.y, i4.z-m4.z).toFixed(4)
  };
}
"""


def pose(muneca, extra=None, index_spread=None, middle_spread=None):
    data = {
        "thumb": {"curl": 0.0},
        "index": {"curl": 0.0},
        "middle": {"curl": 0.0},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "muneca": muneca,
        "extra": extra or {T1: {"z": -30}},
    }
    if index_spread is not None:
        data["index"]["spread"] = index_spread
    if middle_spread is not None:
        data["middle"]["spread"] = middle_spread
    return data


CASES = {
    "00_base": pose({"z": 90}),
    "01_z-90": pose({"z": -90}),
    "02_y180": pose({"z": 90, "y": 180}),
    "03_y-90": pose({"y": -90}),
    "04_y90": pose({"y": 90}),
    "05_x180": pose({"z": 90, "x": 180}),
    "06_z90_y90": pose({"z": 90, "y": 90}),
    "07_z90_y-90": pose({"z": 90, "y": -90}),
    "08_z0": pose({"z": 0}, extra={T1: {"z": -30}}),
    "09_thumb-40": pose({"z": 90}, extra={T1: {"z": -40}}),
    "10_thumb-20": pose({"z": 90}, extra={T1: {"z": -20}}),
    "11_tog": pose({"z": 90}, index_spread=6, middle_spread=-6),
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
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name}: thumb={m.get('thumb')} index={m.get('index')} "
                f"i4={m.get('i4')} tog={m.get('together')} hand={m.get('hand')}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '8deg 78deg 0.55m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '55deg 78deg 0.60m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_oblique.png"))

        browser.close()


if __name__ == "__main__":
    main()
