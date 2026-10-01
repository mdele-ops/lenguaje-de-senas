"""M lab 1: tres dedos (indice, medio, anular) hacia abajo; pulgar sujeta el menique."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_m"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=m1"

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
  function dir(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    const len = Math.hypot(dx, dy, dz) || 1;
    return { x: dx / len, y: dy / len, z: dz / len };
  }
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const index = dir(i1, i4);
  return {
    idxDown: index.y,
    idxDir: index,
    togetherIM: Math.hypot(i4.x - m4.x, i4.y - m4.y, i4.z - m4.z),
    togetherMR: Math.hypot(m4.x - r4.x, m4.y - r4.y, m4.z - r4.z),
    pinkyTipY: p4 && p4.y,
    thumbTipY: t4 && t4.y,
    indexTipY: i4 && i4.y,
  };
}
"""


def fingers(muneca=None, extra=None, ic=0.05, mc=0.05, rc=0.05):
    data = {
        "thumb": {"curl": 0.74, "aside": -0.5},
        "index": {"curl": ic, "spread": 8},
        "middle": {"curl": mc},
        "ring": {"curl": rc, "spread": -8},
        "pinky": {"curl": 0.95},
    }
    if muneca:
        data["muneca"] = muneca
    extra_map = {T1: {"y": -60, "x": -12}}
    if extra:
        extra_map.update(extra)
    data["extra"] = extra_map
    return data


CASES = {
    "00_current": {
        "thumb": {"curl": 0.85, "twist": -8},
        "index": {"curl": 0.85},
        "middle": {"curl": 0.85},
        "ring": {"curl": 0.85},
        "pinky": {"curl": 0.85},
    },
    "01_up": fingers(),
    "02_x60": fingers(muneca={"x": 60}),
    "03_x80": fingers(muneca={"x": 80}),
    "04_x100": fingers(muneca={"x": 100}),
    "05_x-60": fingers(muneca={"x": -60}),
    "06_x-80": fingers(muneca={"x": -80}),
    "07_z90": fingers(muneca={"z": 90}),
    "08_z90_x60": fingers(muneca={"z": 90, "x": 60}),
    "09_z90_x-60": fingers(muneca={"z": 90, "x": -60}),
    "10_y180": fingers(muneca={"y": 180}),
    "11_y180_x70": fingers(muneca={"y": 180, "x": 70}),
    "12_x90_z20": fingers(muneca={"x": 90, "z": 20}),
    "13_x70_y20": fingers(muneca={"x": 70, "y": 20}),
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
                f"{name:14s}  idxDown={m['idxDown']:+.3f}  "
                f"togIM={m['togetherIM']:.3f} togMR={m['togetherMR']:.3f}  "
                f"iY={m['indexTipY']:+.3f} tY={m['thumbTipY']:+.3f} pY={m['pinkyTipY']:+.3f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.08m 2.36m 0.20m';
                    mv.cameraOrbit = '18deg 78deg 0.55m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '-18deg 82deg 0.58m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.10)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        browser.close()


if __name__ == "__main__":
    main()
