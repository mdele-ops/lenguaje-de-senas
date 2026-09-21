"""F: pulgar vertical (no horizontal) y yema del indice tocando el pulgar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f13"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f13v"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

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
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const dx = t4.x - i4.x, dy = t4.y - i4.y, dz = t4.z - i4.z;
  return {
    dist: Math.sqrt(dx*dx + dy*dy + dz*dz),
    dx, dy, dz,
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
    "00_actual": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}),
    "01_no_extra": pose(0.12, 0.22, 0.58),
    "02_curl0": pose(0.00, 0.20, 0.62),
    "03_y-40": pose(0.12, 0.10, 0.60, {T1: {"y": -40}}),
    "04_y-50": pose(0.10, 0.05, 0.62, {T1: {"y": -50}}),
    "05_y-60": pose(0.08, 0.00, 0.64, {T1: {"y": -60}}),
    "06_b_like": pose(0.74, -0.50, 0.66, {T1: {"y": -60}}),
    "07_b_soft": pose(0.40, -0.35, 0.62, {T1: {"y": -45}}),
    "08_y-55_c20": pose(0.20, -0.20, 0.64, {T1: {"y": -55}}),
    "09_y-48_c08": pose(0.08, 0.08, 0.68, {T1: {"y": -48}}),
    "10_y-48_i72": pose(0.08, 0.08, 0.72, {T1: {"y": -48}}),
    "11_y-48_i78": pose(0.08, 0.08, 0.78, {T1: {"y": -48}}),
    "12_y-35_c05": pose(0.05, 0.15, 0.66, {T1: {"y": -35}}),
    "13_z-8_y-40": pose(0.10, 0.10, 0.64, {T1: {"z": -8, "y": -40}}),
    "14_z8_y-40": pose(0.10, 0.10, 0.64, {T1: {"z": 8, "y": -40}}),
    "15_y-52_s6": pose(0.08, 0.05, 0.70, {T1: {"y": -52}}, i_spread=6),
    "16_y-52_s-6": pose(0.08, 0.05, 0.70, {T1: {"y": -52}}, i_spread=-6),
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
                f"{name}: dist={m['dist']:.4f} up={m['thumbUp']:.3f} "
                f"horiz={m['thumbHoriz']:.3f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        print("best (high up + low dist):")
        scored = sorted(
            ranked,
            key=lambda x: (1 - max(0.0, x[1]["thumbUp"])) * 0.10 + x[1]["dist"],
        )
        for name, m in scored[:8]:
            print(
                f"  {name}: dist={m['dist']:.4f} up={m['thumbUp']:.3f} horiz={m['thumbHoriz']:.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
