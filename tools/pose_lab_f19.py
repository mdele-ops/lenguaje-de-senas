"""Parte de 17 (yemas cerca, sin wrap) y cierra el hueco en Z."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f19"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f19c"

T1 = "mixamorig1RightHandThumb1_036"
T3 = "mixamorig1RightHandThumb3_038"
I1 = "mixamorig1RightHandIndex1_040"
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
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const distTip = dist(t4, i4);
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  return {
    distTip, distShaft,
    wrap: distShaft + 0.001 < distTip * 0.55,
    dx: t4.x - i4.x, dy: t4.y - i4.y, dz: t4.z - i4.z,
    thumbUp: tdy / tlen
  };
}
"""


def pose(t_curl, i_curl, spread=6, extra=None):
    extra_data = {T1: {"z": 30}}
    if extra:
        extra_data.update(extra)
    return {
        "thumb": {"curl": t_curl},
        "index": {"curl": i_curl, "spread": spread},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra_data,
    }


CASES = {
    "00_17": pose(0.18, 0.50, 6),
    "01_t20_i50": pose(0.20, 0.50, 6),
    "02_t22_i50": pose(0.22, 0.50, 6),
    "03_t18_i52": pose(0.18, 0.52, 6),
    "04_t20_i48": pose(0.20, 0.48, 6),
    "05_s8": pose(0.18, 0.50, 8),
    "06_s10": pose(0.18, 0.50, 10),
    "07_s4": pose(0.18, 0.50, 4),
    "08_t3z8": pose(0.18, 0.50, 6, {T3: {"z": 8}}),
    "09_t3z-8": pose(0.18, 0.50, 6, {T3: {"z": -8}}),
    "10_i2x8": pose(0.18, 0.50, 6, {I2: {"x": 8}}),
    "11_i2x-8": pose(0.18, 0.50, 6, {I2: {"x": -8}}),
    "12_t22_s8": pose(0.22, 0.50, 8),
    "13_t20_s8": pose(0.20, 0.50, 8),
    "14_t16_i50_s8": pose(0.16, 0.50, 8),
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
            wrap = "WRAP" if m["wrap"] else "ok"
            print(
                f"{name}: tip={m['distTip']:.4f} shaft={m['distShaft']:.4f} {wrap} "
                f"up={m['thumbUp']:.3f} dx={m['dx']:+.3f} dy={m['dy']:+.3f} dz={m['dz']:+.3f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '12deg 76deg 0.40m';
                    mv.fieldOfView = '16deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_tips.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '8deg 78deg 0.50m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))

        print("best (no wrap, small tip, small |dz|):")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1]["wrap"] else 0,
                abs(x[1]["dz"]) * 0.5 + x[1]["distTip"],
            ),
        )
        for name, m in scored[:8]:
            wrap = "WRAP" if m["wrap"] else "ok"
            print(
                f"  {name}: tip={m['distTip']:.4f} shaft={m['distShaft']:.4f} {wrap} "
                f"up={m['thumbUp']:.3f} dz={m['dz']:+.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
