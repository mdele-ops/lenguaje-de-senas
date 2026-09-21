"""F: pulgar vertical al frente (primero), indice al medio detras, hueco."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f28"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f28ord"

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
  const dz = i4.z - mid.z;
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  return {
    distShaft, distMid: dist(i4, mid), distTip: dist(i4, t4),
    dx: i4.x - mid.x, dy: i4.y - mid.y, dz,
    thumbUp: tdy / tlen,
    fused: distShaft < 0.038,
    midHit: distShaft + 0.008 < dist(i4, t4),
    thumbFront: dz < 0.02
  };
}
"""


def pose(i_curl, i2x=20, i2z=-16, i3z=-18, t1=None):
    extra = {T1: t1 or {"z": 30}, I2: {"z": i2z, "x": i2x}, I3: {"z": i3z}}
    return {
        "thumb": {"curl": 0.0},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra,
    }


CASES = {
    "00_actual": pose(0.62, i2x=-20, i2z=-22, i3z=-26),
    "01_i55_x0": pose(0.55, i2x=0, i2z=-14, i3z=-16),
    "02_i55_x16": pose(0.55, i2x=16),
    "03_i55_x20": pose(0.55, i2x=20),
    "04_i55_x24": pose(0.55, i2x=24),
    "05_i58_x16": pose(0.58, i2x=16),
    "06_i58_x20": pose(0.58, i2x=20),
    "07_i58_x24": pose(0.58, i2x=24),
    "08_i58_x28": pose(0.58, i2x=28),
    "09_i52_x20": pose(0.52, i2x=20),
    "10_i52_x24": pose(0.52, i2x=24),
    "11_i58_x20_t1x8": pose(0.58, i2x=20, t1={"z": 30, "x": 8}),
    "12_i58_x24_t1x8": pose(0.58, i2x=24, t1={"z": 30, "x": 8}),
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
            layer = "THUMB-FRONT" if m["thumbFront"] else "idx-front"
            fused = "FUSED" if m["fused"] else "gap"
            mid = "MID" if m["midHit"] else "tip"
            print(
                f"{name}: {layer} {mid} shaft={m['distShaft']:.4f} tip={m['distTip']:.4f} "
                f"{fused} up={m['thumbUp']:.3f} dz={m['dz']:+.3f}"
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

        print("ranked thumb-first + mid + gap:")
        scored = sorted(
            ranked,
            key=lambda x: (
                0 if x[1]["thumbFront"] else 1,
                0 if x[1]["midHit"] else 1,
                1 if x[1]["fused"] else 0,
                1 if x[1]["thumbUp"] < 0.90 else 0,
                abs(x[1]["distShaft"] - 0.05),
            ),
        )
        for name, m in scored:
            layer = "THUMB-FRONT" if m["thumbFront"] else "idx-front"
            fused = "FUSED" if m["fused"] else "gap"
            mid = "MID" if m["midHit"] else "tip"
            print(
                f"  {name}: {layer} {mid} shaft={m['distShaft']:.4f} {fused} "
                f"up={m['thumbUp']:.3f} dz={m['dz']:+.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
