"""K lab 1: medir que eje de muneca mueve la mano hacia enfrente/atras."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_k"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=k1"

FORE = "mixamorig1RightForeArm_034"

K_FINGERS = {
    "thumb": {"curl": 0.25, "aside": 0.2},
    "index": {"curl": 0.0},
    "middle": {"curl": 0.4},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.95},
}

CASES = {
    "00_K": {},
    "x-25": {"muneca": {"x": -25}},
    "x25": {"muneca": {"x": 25}},
    "x-40": {"muneca": {"x": -40}},
    "x40": {"muneca": {"x": 40}},
    "y-25": {"muneca": {"y": -25}},
    "y25": {"muneca": {"y": 25}},
    "z-25": {"muneca": {"z": -25}},
    "z25": {"muneca": {"z": 25}},
    "fx-20": {"extra": {FORE: {"x": -20}}},
    "fx20": {"extra": {FORE: {"x": 20}}},
    "fy-20": {"extra": {FORE: {"y": -20}}},
    "fy20": {"extra": {FORE: {"y": 20}}},
    "fz-20": {"extra": {FORE: {"z": -20}}},
    "fz20": {"extra": {FORE: {"z": 20}}},
    "x25_fx15": {"muneca": {"x": 25}, "extra": {FORE: {"x": 15}}},
    "x-25_fx-15": {"muneca": {"x": -25}, "extra": {FORE: {"x": -15}}},
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
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const hand = pos('mixamorig1RightHand_035');
  if (!i1 || !i4) return { error: 'bones' };
  const dx = i4.x - i1.x, dy = i4.y - i1.y, dz = i4.z - i1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return {
    tip: i4,
    base: i1,
    hand: hand,
    dir: { x: dx / len, y: dy / len, z: dz / len },
  };
}
"""


def pose_with(cfg):
    data = dict(K_FINGERS)
    data.update(cfg)
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
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '0m 2.38m 0.15m';
                mv.cameraOrbit = '8deg 84deg 2.15m';
                mv.fieldOfView = '28deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.2)

        for name, cfg in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose_with(cfg),
            )
            time.sleep(0.22)
            m = page.evaluate(MEASURE_JS)
            t = m["tip"]
            d = m["dir"]
            print(
                f"{name:14s}  tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f})  "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))

        browser.close()


if __name__ == "__main__":
    main()
