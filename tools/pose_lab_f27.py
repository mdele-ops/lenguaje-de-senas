"""F: primero el pulgar (vertical y al frente), despues el indice al medio."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f27"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f27thumb"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
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
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const dz = i4.z - mid.z;
  return {
    distShaft: Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid)),
    distMid: dist(i4, mid),
    distTip: dist(i4, t4),
    dx: i4.x - mid.x, dy: i4.y - mid.y, dz,
    thumbUp: tdy / tlen,
    fused: Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid)) < 0.038,
    thumbFront: dz < -0.01
  };
}
"""


def pose(thumb=None, i_curl=0.0, extra=None, aside=None):
    t = {"curl": 0.0}
    if thumb:
        t.update(thumb)
    if aside is not None:
        t["aside"] = aside
    extra_data = extra or {}
    return {
        "thumb": t,
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra_data,
    }


# Fase 1: solo pulgar (indice extendido) para verlo vertical y al frente.
# Fase 2: con el pulgar fijo, el indice se acerca al medio, detras.
CASES = {
    "00_actual": pose(
        i_curl=0.62,
        extra={T1: {"z": 30}, I2: {"z": -22, "x": -20}, I3: {"z": -26}},
    ),
    "01_thumb_only_z30": pose(extra={T1: {"z": 30}}),
    "02_thumb_only_z40": pose(extra={T1: {"z": 40}}),
    "03_thumb_only_z30_x12": pose(extra={T1: {"z": 30, "x": 12}}),
    "04_thumb_only_z30_x-12": pose(extra={T1: {"z": 30, "x": -12}}),
    "05_thumb_only_z30_y-20": pose(extra={T1: {"z": 30, "y": -20}}),
    "06_thumb_b": pose(
        thumb={"curl": 0.74},
        aside=-0.5,
        extra={T1: {"y": -60}},
    ),
    "07_t_z30_i55": pose(i_curl=0.55, extra={T1: {"z": 30}}),
    "08_t_z30_i62": pose(i_curl=0.62, extra={T1: {"z": 30}}),
    "09_t_z30_i70": pose(i_curl=0.70, extra={T1: {"z": 30}}),
    "10_t_z30_i55_open": pose(
        i_curl=0.55,
        extra={T1: {"z": 30}, I2: {"z": -18}, I3: {"z": -20}},
    ),
    "11_t_z30_x12_i58": pose(
        i_curl=0.58,
        extra={T1: {"z": 30, "x": 12}, I2: {"z": -16}, I3: {"z": -18}},
    ),
    "12_t_z30_x-12_i58": pose(
        i_curl=0.58,
        extra={T1: {"z": 30, "x": -12}, I2: {"z": -16}, I3: {"z": -18}},
    ),
    "13_t_z30_i58_i2x20": pose(
        i_curl=0.58,
        extra={T1: {"z": 30}, I2: {"z": -16, "x": 20}, I3: {"z": -18}},
    ),
    "14_t_z30_i58_i2x32": pose(
        i_curl=0.58,
        extra={T1: {"z": 30}, I2: {"z": -16, "x": 32}, I3: {"z": -18}},
    ),
    "15_t_z30_y-20_i58": pose(
        i_curl=0.58,
        extra={T1: {"z": 30, "y": -20}, I2: {"z": -16}, I3: {"z": -18}},
    ),
    "16_b_i55": pose(
        thumb={"curl": 0.74},
        aside=-0.5,
        i_curl=0.55,
        extra={T1: {"y": -60}, I2: {"z": -16}, I3: {"z": -18}},
    ),
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
            print(
                f"{name}: {layer} shaft={m['distShaft']:.4f} tip={m['distTip']:.4f} "
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

        print("best thumb-first (front, gap, vertical):")
        scored = sorted(
            ranked,
            key=lambda x: (
                0 if x[1]["thumbFront"] else 1,
                1 if x[1]["fused"] else 0,
                1 if x[1]["thumbUp"] < 0.88 else 0,
                abs(x[1]["distShaft"] - 0.05),
            ),
        )
        for name, m in scored:
            layer = "THUMB-FRONT" if m["thumbFront"] else "idx-front"
            fused = "FUSED" if m["fused"] else "gap"
            print(
                f"  {name}: {layer} shaft={m['distShaft']:.4f} {fused} "
                f"up={m['thumbUp']:.3f} dz={m['dz']:+.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
