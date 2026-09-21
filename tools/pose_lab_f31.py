"""F: yema toca el indice con hueco visible, sin clip."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f31"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f31gap"

T1 = "mixamorig1RightHandThumb1_036"
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
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t3 = pos('mixamorig1RightHandThumb3_038');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i2 = pos('mixamorig1RightHandIndex2_041');
  const i3 = pos('mixamorig1RightHandIndex3_042');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const distTip = dist(t4, i4);
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  const yemaToIndex = Math.min(dist(t4, i2), dist(t4, i3), dist(t4, i4));
  return {
    distTip, distShaft, yemaToIndex,
    thumbUp: tdy / tlen,
    wrap: distShaft + 0.001 < distTip * 0.55,
    clip: yemaToIndex < 0.045,
    touch: yemaToIndex >= 0.045 && yemaToIndex <= 0.070
  };
}
"""


def pose(i_curl, extra=None, spread=None):
    index = {"curl": i_curl}
    if spread is not None:
        index["spread"] = spread
    return {
        "thumb": {"curl": 0.0},
        "index": index,
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra or {T1: {"z": 30}},
    }


CASES = {
    "00_actual": pose(0.70, {T1: {"z": 30}, I2: {"x": 8}}),
    "01_08": pose(0.52, {T1: {"z": 30}, I2: {"z": -14}, I3: {"z": -16}}),
    "02_open20": pose(0.52, {T1: {"z": 30}, I2: {"z": -20}, I3: {"z": -24}}),
    "03_i50_open16": pose(0.50, {T1: {"z": 30}, I2: {"z": -16}, I3: {"z": -18}}),
    "04_i52_s6": pose(0.52, {T1: {"z": 30}, I2: {"z": -14}, I3: {"z": -16}}, spread=6),
    "05_i52_s-6": pose(0.52, {T1: {"z": 30}, I2: {"z": -14}, I3: {"z": -16}}, spread=-6),
    "06_i48_open12": pose(0.48, {T1: {"z": 30}, I2: {"z": -12}, I3: {"z": -14}}),
    "07_i52_i1y8": pose(0.52, {T1: {"z": 30}, I1: {"y": 8}, I2: {"z": -14}, I3: {"z": -16}}),
    "08_i52_i1y-8": pose(0.52, {T1: {"z": 30}, I1: {"y": -8}, I2: {"z": -14}, I3: {"z": -16}}),
    "09_i45": pose(0.45, {T1: {"z": 30}}),
    "10_i40": pose(0.40, {T1: {"z": 30}}),
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
            if m["touch"]:
                flags.append("TOUCH")
            if m["wrap"]:
                flags.append("WRAP")
            if m["clip"]:
                flags.append("CLIP")
            flag = " ".join(flags) or "far"
            print(
                f"{name}: yema={m['yemaToIndex']:.4f} tip={m['distTip']:.4f} "
                f"shaft={m['distShaft']:.4f} {flag} up={m['thumbUp']:.3f}"
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
                    mv.cameraOrbit = '-40deg 80deg 0.52m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))

        print("best:")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1]["wrap"] else 0,
                1 if x[1]["clip"] else 0,
                0 if x[1]["touch"] else 1,
                abs(x[1]["yemaToIndex"] - 0.055),
            ),
        )
        for name, m in scored:
            flags = []
            if m["touch"]:
                flags.append("TOUCH")
            if m["wrap"]:
                flags.append("WRAP")
            if m["clip"]:
                flags.append("CLIP")
            flag = " ".join(flags) or "far"
            print(
                f"  {name}: yema={m['yemaToIndex']:.4f} tip={m['distTip']:.4f} "
                f"shaft={m['distShaft']:.4f} {flag} up={m['thumbUp']:.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
