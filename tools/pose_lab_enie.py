"""Ñ lab 1: qué eje mueve la mano de izquierda a derecha sin deformar la seña."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_enie"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=enie1"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"

ENIE = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.12, "spread": 9},
    "middle": {"curl": 0.12, "spread": -3},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.95},
    "muneca": {"x": 150, "y": 12},
    "extra": {
        "mixamorig1RightHandThumb1_036": {"y": -60, "x": -12},
        "mixamorig1RightHandRing1_048": {"x": 8},
        "mixamorig1RightHandRing2_049": {"x": 24},
        "mixamorig1RightHandRing3_050": {"x": 26},
        "mixamorig1RightHandPinky1_052": {"x": 8},
        "mixamorig1RightHandPinky2_053": {"x": 24},
        "mixamorig1RightHandPinky3_054": {"x": 26},
        ARM: {"z": -18},
    },
}

CASES = {
    "00_base": {},
    "wy-20": {"muneca": {"y": -8}},
    "wy32": {"muneca": {"y": 32}},
    "wz-25": {"muneca": {"z": -25}},
    "wz25": {"muneca": {"z": 25}},
    "arm_z0": {"extra": {ARM: {"z": 0}}},
    "arm_z-36": {"extra": {ARM: {"z": -36}}},
    "arm_y-20": {"extra": {ARM: {"y": -20}}},
    "arm_y20": {"extra": {ARM: {"y": 20}}},
    "fore_y-20": {"extra": {FORE: {"y": -20}}},
    "fore_y20": {"extra": {FORE: {"y": 20}}},
    "fore_z-20": {"extra": {FORE: {"z": -20}}},
    "fore_z20": {"extra": {FORE: {"z": 20}}},
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
  if (!i1 || !i4 || !hand) return { error: 'bones' };
  const dx = i4.x - i1.x, dy = i4.y - i1.y, dz = i4.z - i1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return { tip: i4, hand: hand, dir: { x: dx / len, y: dy / len, z: dz / len } };
}
"""


def merge_extra(base, patch):
    out = {k: dict(v) for k, v in base.items()}
    for name, rots in (patch or {}).items():
        out[name] = dict(out.get(name, {}))
        out[name].update(rots)
    return out


def pose_with(cfg):
    data = {k: v for k, v in ENIE.items()}
    if "muneca" in cfg:
        data["muneca"] = dict(ENIE["muneca"], **cfg["muneca"])
    data["extra"] = merge_extra(ENIE["extra"], cfg.get("extra"))
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
                mv.cameraOrbit = '0deg 84deg 2.15m';
                mv.fieldOfView = '30deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.3)

        base = None
        for name, cfg in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose_with(cfg),
            )
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            if m.get("error"):
                print(f"{name:12s}  ERROR {m['error']}")
                continue
            t, h, d = m["tip"], m["hand"], m["dir"]
            if base is None:
                base = (t, h)
            print(
                f"{name:12s}  tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f})  "
                f"d_tip=({t['x'] - base[0]['x']:+.3f},{t['y'] - base[0]['y']:+.3f},{t['z'] - base[0]['z']:+.3f})  "
                f"d_mano=({h['x'] - base[1]['x']:+.3f},{h['y'] - base[1]['y']:+.3f},{h['z'] - base[1]['z']:+.3f})  "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))

        browser.close()


if __name__ == "__main__":
    main()
