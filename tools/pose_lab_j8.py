"""J lab 8: bajar el meñique (antebrazo) y luego el gancho (muneca) para dibujar una J legible."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j8"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j8"

T1 = "mixamorig1RightHandThumb1_036"
FORE = "mixamorig1RightForeArm_034"
ARM = "mixamorig1RightArm_033"
THUMB_EXTRA = {T1: {"y": -60, "x": -12}}

FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
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
  const p1 = pos('mixamorig1RightHandPinky1_052');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  if (!p1 || !p4) return { error: 'bones' };
  const dx = p4.x - p1.x, dy = p4.y - p1.y, dz = p4.z - p1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return { tip: p4, dir: { x: dx / len, y: dy / len, z: dz / len } };
}
"""

PROBE = {
    "00_I": {},
    "fx25": {"extra": {FORE: {"x": 25}}},
    "fx-25": {"extra": {FORE: {"x": -25}}},
    "fy25": {"extra": {FORE: {"y": 25}}},
    "fy-25": {"extra": {FORE: {"y": -25}}},
    "fz25": {"extra": {FORE: {"z": 25}}},
    "fz-25": {"extra": {FORE: {"z": -25}}},
    "ax15": {"extra": {ARM: {"x": 15}}},
    "ax-15": {"extra": {ARM: {"x": -15}}},
    "az15": {"extra": {ARM: {"z": 15}}},
    "az-15": {"extra": {ARM: {"z": -15}}},
}


def pose(muneca=None, extra=None):
    data = dict(FINGERS)
    merged = dict(THUMB_EXTRA)
    if extra:
        for k, v in extra.items():
            if k in merged:
                merged[k] = dict(merged[k], **v)
            else:
                merged[k] = v
    data["extra"] = merged
    if muneca:
        data["muneca"] = muneca
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
        time.sleep(0.8)

        viewer = page.query_selector("#viewer")
        print("=== probe brazo/antebrazo ===")
        for name, cfg in PROBE.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose(extra=cfg.get("extra"), muneca=cfg.get("muneca")),
            )
            time.sleep(0.18)
            m = page.evaluate(MEASURE_JS)
            t = m["tip"]
            d = m["dir"]
            print(
                f"{name:10s} tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f}) "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.40m 0.15m';
                    mv.cameraOrbit = '8deg 84deg 2.2m';
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.1)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))

        browser.close()


if __name__ == "__main__":
    main()
