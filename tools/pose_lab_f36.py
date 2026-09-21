"""F: pulgar PEGADO vertical (estilo B) e indice rozando el medio."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f36"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f36peg"

T1 = "mixamorig1RightHandThumb1_036"
I2 = "mixamorig1RightHandIndex2_041"

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
  const m4 = pos('mixamorig1RightHandMiddle4_047');
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
  const distMidFinger = m4 ? dist(i4, m4) : 9;
  return {
    distTip, distShaft, distMidFinger,
    distMid: dist(i4, mid),
    thumbUp: tdy / tlen,
    thumbHoriz: Math.sqrt(tdx*tdx + tdz*tdz) / tlen,
    clip: distShaft < 0.038
  };
}
"""


def pose(t_curl, aside, i_curl, extra, i_spread=None):
    index = {"curl": i_curl}
    if i_spread is not None:
        index["spread"] = i_spread
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": index,
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra,
    }


CASES = {
    "00_v62": pose(0.0, 0.0, 0.62, {T1: {"z": 30}, I2: {"x": 8}}),
    "01_b_i50": pose(0.74, -0.5, 0.50, {T1: {"y": -60}}),
    "02_b_i58": pose(0.74, -0.5, 0.58, {T1: {"y": -60}}),
    "03_b0_i55": pose(0.0, -0.5, 0.55, {T1: {"y": -60}}),
    "04_b0_i62": pose(0.0, -0.5, 0.62, {T1: {"y": -60}}),
    "05_b20_i55": pose(0.20, -0.45, 0.55, {T1: {"y": -60, "z": 12}}),
    "06_z30_y-40": pose(0.0, -0.25, 0.58, {T1: {"z": 30, "y": -40}, I2: {"x": 8}}),
    "07_z30_y-50": pose(0.0, -0.35, 0.58, {T1: {"z": 30, "y": -50}, I2: {"x": 6}}),
    "08_b_i52_s-8": pose(0.60, -0.5, 0.52, {T1: {"y": -60}}, i_spread=-8),
    "09_peg": pose(0.40, -0.45, 0.58, {T1: {"y": -55, "z": 18}, I2: {"x": 6}}),
    "10_peg2": pose(0.15, -0.40, 0.60, {T1: {"y": -48, "z": 24}, I2: {"x": 8}}),
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
            flag = "CLIP" if m.get("clip") else ""
            print(
                f"{name}: up={m['thumbUp']:.3f} horiz={m['thumbHoriz']:.3f} "
                f"shaft={m['distShaft']:.4f} tip={m['distTip']:.4f} "
                f"i-mid={m['distMidFinger']:.4f} {flag}"
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
                    mv.cameraOrbit = '0deg 72deg 0.48m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        print("ranked (high up, low horiz, shaft graze ~0.05, tip not glued):")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1].get("clip") else 0,
                1 if x[1]["thumbUp"] < 0.80 else 0,
                x[1]["thumbHoriz"],
                abs(x[1]["distShaft"] - 0.050),
                abs(x[1]["distTip"] - 0.080),
            ),
        )
        for name, m in scored:
            flag = "CLIP" if m.get("clip") else ""
            print(
                f"  {name}: up={m['thumbUp']:.3f} horiz={m['thumbHoriz']:.3f} "
                f"shaft={m['distShaft']:.4f} tip={m['distTip']:.4f} {flag}"
            )
        browser.close()


if __name__ == "__main__":
    main()
