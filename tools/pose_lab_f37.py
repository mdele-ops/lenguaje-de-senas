"""F: misma pose, solo desenlazar pulgar e indice (hueco, sin clip)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f37"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f37gap"

T1 = "mixamorig1RightHandThumb1_036"
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
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t3 = pos('mixamorig1RightHandThumb3_038');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const distTip = dist(i4, t4);
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  return {
    distTip, distShaft, distMid: dist(i4, mid),
    thumbUp: tdy / tlen,
    linked: distShaft < 0.055,
    graze: distShaft >= 0.055 && distShaft <= 0.078,
    far: distShaft > 0.078
  };
}
"""


def pose(i_curl, extra):
    return {
        "thumb": {"curl": 0.0},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 4},
        "ring": {"curl": 0.0, "spread": 5},
        "pinky": {"curl": 0.0, "spread": 8},
        "extra": extra,
    }


CASES = {
    "00_actual": pose(0.62, {T1: {"z": 30}, I2: {"x": 8}}),
    "01_i58": pose(0.58, {T1: {"z": 30}, I2: {"x": 8}}),
    "02_i56": pose(0.56, {T1: {"z": 30}, I2: {"x": 8}}),
    "03_i54": pose(0.54, {T1: {"z": 30}, I2: {"x": 8}}),
    "04_i58_x4": pose(0.58, {T1: {"z": 30}, I2: {"x": 4}}),
    "05_i56_x4": pose(0.56, {T1: {"z": 30}, I2: {"x": 4}}),
    "06_i58_z-10": pose(0.58, {T1: {"z": 30}, I2: {"x": 8, "z": -10}}),
    "07_i56_z-12": pose(0.56, {T1: {"z": 30}, I2: {"x": 6, "z": -12}}),
    "08_i55_z-8": pose(0.55, {T1: {"z": 30}, I2: {"x": 6, "z": -8}}),
    "09_i57_i3z": pose(0.57, {T1: {"z": 30}, I2: {"x": 6, "z": -10}, I3: {"z": -8}}),
    "10_i52": pose(0.52, {T1: {"z": 30}, I2: {"x": 6}}),
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
        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            flags = []
            if m.get("linked"):
                flags.append("LINKED")
            if m.get("graze"):
                flags.append("GRAZE")
            if m.get("far"):
                flags.append("FAR")
            flag = " ".join(flags)
            print(
                f"{name}: shaft={m['distShaft']:.4f} mid={m['distMid']:.4f} "
                f"tip={m['distTip']:.4f} {flag} up={m['thumbUp']:.3f}"
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
                    mv.cameraOrbit = '-35deg 78deg 0.50m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '0deg 72deg 0.46m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        print("ranked (graze, not linked, keep vertical):")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1].get("linked") else 0,
                1 if x[1].get("far") else 0,
                0 if x[1].get("graze") else 1,
                abs(x[1]["distShaft"] - 0.064),
                1 if x[1]["thumbUp"] < 0.90 else 0,
            ),
        )
        for name, m in scored:
            flags = []
            if m.get("linked"):
                flags.append("LINKED")
            if m.get("graze"):
                flags.append("GRAZE")
            if m.get("far"):
                flags.append("FAR")
            print(
                f"  {name}: shaft={m['distShaft']:.4f} tip={m['distTip']:.4f} "
                f"{' '.join(flags)} up={m['thumbUp']:.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
