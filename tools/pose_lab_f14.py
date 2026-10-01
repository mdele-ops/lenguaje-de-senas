"""F: pulgar vertical como en B (y -60, aside negativo), sin tumbarlo de lado.
El indice se cierra contra el fuste del pulgar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f14"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f14v"

T1 = "mixamorig1RightHandThumb1_036"
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
  function distTo(p) {
    const dx = i4.x - p.x, dy = i4.y - p.y, dz = i4.z - p.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const d2 = distTo(t2), d3 = distTo(t3), d4 = distTo(t4);
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const dmid = distTo(mid);
  const nearest = Math.min(d2, d3, d4, dmid);
  return {
    distTip: d4,
    distMid: dmid,
    distNearest: nearest,
    dx: i4.x - t4.x, dy: i4.y - t4.y, dz: i4.z - t4.z,
    thumbUp: tdy / tlen,
    thumbHoriz: Math.sqrt(tdx*tdx + tdz*tdz) / tlen
  };
}
"""


def pose(t_curl, aside, i_curl, extra=None, i_spread=None):
    data = {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
    }
    if i_spread is not None:
        data["index"]["spread"] = i_spread
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_actual": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, "mixamorig1RightHandThumb2_037": {"x": -36}}),
    "01_b_i55": pose(0.74, -0.50, 0.55, {T1: {"y": -60}}),
    "02_b_i62": pose(0.74, -0.50, 0.62, {T1: {"y": -60}}),
    "03_b_i70": pose(0.74, -0.50, 0.70, {T1: {"y": -60}}),
    "04_b_i78": pose(0.74, -0.50, 0.78, {T1: {"y": -60}}),
    "05_ext_y60": pose(0.05, -0.50, 0.62, {T1: {"y": -60}}),
    "06_ext_y60_i70": pose(0.05, -0.50, 0.70, {T1: {"y": -60}}),
    "07_ext_y60_i78": pose(0.08, -0.50, 0.78, {T1: {"y": -60}}),
    "08_c20_y60": pose(0.20, -0.50, 0.66, {T1: {"y": -60}}),
    "09_c30_y60": pose(0.30, -0.50, 0.64, {T1: {"y": -60}}),
    "10_c40_y60": pose(0.40, -0.45, 0.62, {T1: {"y": -60}}),
    "11_c20_y70": pose(0.12, -0.50, 0.68, {T1: {"y": -70}}),
    "12_c10_y55": pose(0.10, -0.45, 0.66, {T1: {"y": -55}}),
    "13_ext_i1x12": pose(0.08, -0.50, 0.68, {T1: {"y": -60}, I1: {"x": 12}}),
    "14_ext_i1x-12": pose(0.08, -0.50, 0.68, {T1: {"y": -60}, I1: {"x": -12}}),
    "15_ext_i2x16": pose(0.08, -0.50, 0.70, {T1: {"y": -60}, I2: {"x": 16}}),
    "16_c15_as-35_y60": pose(0.15, -0.35, 0.68, {T1: {"y": -60}}),
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

        def cam(target, orbit, fov):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.16)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            print(
                f"{name}: near={m['distNearest']:.4f} mid={m['distMid']:.4f} "
                f"tip={m['distTip']:.4f} up={m['thumbUp']:.3f} horiz={m['thumbHoriz']:.3f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        print("best vertical + contact:")
        scored = sorted(
            ranked,
            key=lambda x: (1 - max(0.0, x[1]["thumbUp"])) * 0.12 + x[1]["distNearest"],
        )
        for name, m in scored[:8]:
            print(
                f"  {name}: near={m['distNearest']:.4f} up={m['thumbUp']:.3f} horiz={m['thumbHoriz']:.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
