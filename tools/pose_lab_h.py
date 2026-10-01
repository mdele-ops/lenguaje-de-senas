"""H: indice+medio horizontales juntos, pulgar ARRIBA, anular y menique cerrados."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_h"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=h1"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
HAND = "mixamorig1RightHand_035"

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
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  function dir(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    const len = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1;
    return { dx, dy, dz, len, up: dy / len, horiz: Math.sqrt(dx*dx + dz*dz) / len };
  }
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m1 = pos('mixamorig1RightHandMiddle1_044');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  if (!t1 || !t4 || !i1 || !i4 || !m4) return { error: 'bones' };
  const thumb = dir(t1, t4);
  const index = dir(i1, i4);
  const middle = dir(m1, m4);
  return {
    thumbUp: thumb.up,
    thumbHoriz: thumb.horiz,
    indexHoriz: index.horiz,
    indexUp: index.up,
    middleHoriz: middle.horiz,
    together: dist(i4, m4),
    ringClosed: dist(r4, i1),
    pinkyClosed: dist(p4, i1)
  };
}
"""


def pose(thumb=None, extra=None, muneca=None, index_spread=None, middle_spread=None):
    data = {
        "thumb": thumb if thumb is not None else {"curl": 0.0},
        "index": {"curl": 0.0},
        "middle": {"curl": 0.0},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "muneca": muneca if muneca is not None else {"z": 90},
    }
    if index_spread is not None:
        data["index"]["spread"] = index_spread
    if middle_spread is not None:
        data["middle"]["spread"] = middle_spread
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_actual": {
        "thumb": {"curl": 0.55},
        "index": {"curl": 0.05},
        "middle": {"curl": 0.05},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "muneca": {"z": 90},
    },
    "01_thumb0": pose({"curl": 0.0}),
    "02_thumb0_aside": pose({"curl": 0.0, "aside": 0.35}),
    "03_t1z30": pose({"curl": 0.0}, extra={T1: {"z": 30}}),
    "04_t1z45": pose({"curl": 0.0}, extra={T1: {"z": 45}}),
    "05_t1z-30": pose({"curl": 0.0}, extra={T1: {"z": -30}}),
    "06_together": pose({"curl": 0.0}, index_spread=-4, middle_spread=4),
    "07_wrist70": pose({"curl": 0.0}, muneca={"z": 70}),
    "08_wrist110": pose({"curl": 0.0}, muneca={"z": 110}),
    "09_wrist90_x20": pose({"curl": 0.0}, muneca={"z": 90, "x": 20}),
    "10_t1y20": pose({"curl": 0.0}, extra={T1: {"y": 20}}),
    "11_thumb0_z30_tog": pose(
        {"curl": 0.0},
        extra={T1: {"z": 30}},
        index_spread=-4,
        middle_spread=4,
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
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name}: thumbUp={m.get('thumbUp', 0):+.3f} "
                f"idxH={m.get('indexHoriz', 0):.3f} idxUp={m.get('indexUp', 0):+.3f} "
                f"tog={m.get('together', 0):.4f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '8deg 78deg 0.50m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '-40deg 80deg 0.50m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))

        browser.close()


if __name__ == "__main__":
    main()
