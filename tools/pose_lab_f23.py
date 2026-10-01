"""F: misma forma, hueco visible, indice sin giro irreal."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f23"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f23gap"

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
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  function lerp(a, b, t) {
    return { x: a.x+(b.x-a.x)*t, y: a.y+(b.y-a.y)*t, z: a.z+(b.z-a.z)*t };
  }
  let distShaft = 99, closestT = 0;
  const segs = [[t1,t2],[t2,t3],[t3,t4]];
  segs.forEach((seg, si) => {
    for (let k = 0; k <= 8; k++) {
      const p = lerp(seg[0], seg[1], k/8);
      const d = dist(i4, p);
      if (d < distShaft) { distShaft = d; closestT = si + k/8; }
    }
  });
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  return {
    distMid: dist(i4, mid),
    distShaft,
    closestT,
    distTip: dist(i4, t4),
    dx: i4.x - mid.x, dy: i4.y - mid.y, dz: i4.z - mid.z,
    thumbUp: tdy / tlen,
    fused: distShaft < 0.038
  };
}
"""


def pose(i_curl, extra_index=None):
    extra = {T1: {"z": 30}}
    if extra_index:
        extra.update(extra_index)
    return {
        "thumb": {"curl": 0.0},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra,
    }


CASES = {
    "00_actual": pose(0.74, {I2: {"x": 20}}),
    "01_i74_notwist": pose(0.74),
    "02_i62": pose(0.62),
    "03_i55": pose(0.55),
    "04_i48": pose(0.48),
    "05_i58_opentip": pose(0.58, {I3: {"z": -28}}),
    "06_i62_openpip": pose(0.62, {I2: {"z": -22}, I3: {"z": -26}}),
    "07_i52_i1y": pose(0.52, {I1: {"y": 6}}),
    "08_i50": pose(0.50),
    "09_i55_i3z": pose(0.55, {I3: {"z": -22}}),
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
            fused = "FUSED" if m["fused"] else "gap"
            print(
                f"{name}: shaft={m['distShaft']:.4f} mid={m['distMid']:.4f} "
                f"tip={m['distTip']:.4f} {fused} up={m['thumbUp']:.3f} "
                f"t={m['closestT']:.2f} dz={m['dz']:+.3f} dy={m['dy']:+.3f}"
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
                    mv.cameraOrbit = '42deg 78deg 0.48m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))

        print("best natural gap at mid-thumb:")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1]["fused"] else 0,
                1 if x[1]["thumbUp"] < 0.90 else 0,
                abs(x[1]["distShaft"] - 0.055) + abs(x[1]["closestT"] - 1.4) * 0.02,
            ),
        )
        for name, m in scored[:6]:
            fused = "FUSED" if m["fused"] else "gap"
            print(
                f"  {name}: shaft={m['distShaft']:.4f} tip={m['distTip']:.4f} "
                f"{fused} up={m['thumbUp']:.3f} t={m['closestT']:.2f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
