"""F: pulgar vertical; indice toca a media altura del pulgar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f4"

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
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t3 = pos('mixamorig1RightHandThumb3_038');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const idx = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t2 || !t3 || !t4 || !idx) return { error: 'bones' };
  const mid = {
    x: (t2.x + t3.x) / 2,
    y: (t2.y + t3.y) / 2,
    z: (t2.z + t3.z) / 2
  };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const dx = idx.x - mid.x, dy = idx.y - mid.y, dz = idx.z - mid.z;
  return {
    dist: Math.sqrt(dx*dx + dy*dy + dz*dz),
    dx, dy, dz,
    thumbUp: tdy / tlen,
    thumbLen: tlen,
    tipY: t4.y, midY: mid.y, idxY: idx.y
  };
}
"""


def pose(thumb, index, extra=None):
    data = {
        "thumb": thumb,
        "index": index if isinstance(index, dict) else {"curl": index},
        "middle": {"curl": 0.0, "spread": -2},
        "ring": {"curl": 0.0, "spread": -3},
        "pinky": {"curl": 0.0, "spread": -5},
    }
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_actual": pose(
        {"curl": 0.5, "aside": 0.3},
        0.52,
        {T1: {"z": 22, "y": -4}, T2: {"x": -38}},
    ),
    "01_straight": pose({"curl": 0.0, "aside": 0.2}, 0.55),
    "02_b_thumb": pose(
        {"curl": 0.74, "aside": -0.5},
        0.62,
        {T1: {"y": -60}},
    ),
    "03_b_soft": pose(
        {"curl": 0.55, "aside": -0.35},
        0.58,
        {T1: {"y": -40}},
    ),
    "04_up_y-50": pose(
        {"curl": 0.35, "aside": -0.2},
        0.60,
        {T1: {"y": -50}},
    ),
    "05_up_y-30": pose(
        {"curl": 0.25, "aside": 0.1},
        0.58,
        {T1: {"y": -30}},
    ),
    "06_no_t2": pose({"curl": 0.2, "aside": 0.25}, 0.62, {T1: {"z": 8, "y": -10}}),
    "07_aside40": pose({"curl": 0.15, "aside": 0.4}, 0.65),
    "08_b_idx70": pose(
        {"curl": 0.74, "aside": -0.5},
        0.70,
        {T1: {"y": -60}},
    ),
    "09_b_idx78": pose(
        {"curl": 0.74, "aside": -0.5},
        0.78,
        {T1: {"y": -60}},
    ),
    "10_b_idx55": pose(
        {"curl": 0.74, "aside": -0.5},
        0.55,
        {T1: {"y": -60}},
    ),
    "11_up_idx70": pose(
        {"curl": 0.30, "aside": -0.15},
        0.70,
        {T1: {"y": -45}},
    ),
    "12_up_idx50": pose(
        {"curl": 0.20, "aside": 0.0},
        0.50,
        {T1: {"y": -35}},
    ),
    "13_vert_z0": pose({"curl": 0.08, "aside": 0.15}, 0.62, {T1: {"y": -20}}),
    "14_vert_y-55": pose(
        {"curl": 0.45, "aside": -0.4},
        0.66,
        {T1: {"y": -55}},
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
                f"dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        print("best (high up + low dist):")
        scored = sorted(ranked, key=lambda x: (1 - x[1]["thumbUp"]) * 0.08 + x[1]["dist"])
        for name, m in scored[:8]:
            print(f"  {name}: dist={m['dist']:.4f} up={m['thumbUp']:.3f}")
        browser.close()


if __name__ == "__main__":
    main()
