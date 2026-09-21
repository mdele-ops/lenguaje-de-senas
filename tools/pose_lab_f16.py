"""F: pulgar vertical (T1 z~30, curl bajo) e indice cerrando el circulo."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f16"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f16v"

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
  function distTo(p) {
    const dx = i4.x - p.x, dy = i4.y - p.y, dz = i4.z - p.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  return {
    distTip: distTo(t4),
    distMid: distTo(mid),
    distNearest: Math.min(distTo(t2), distTo(t3), distTo(t4), distTo(mid)),
    dx: i4.x - t4.x, dy: i4.y - t4.y, dz: i4.z - t4.z,
    thumbUp: tdy / tlen,
    thumbHoriz: Math.sqrt(tdx*tdx + tdz*tdz) / tlen
  };
}
"""


def pose(i_curl, z=30, t_curl=0.0, extra=None, i_spread=None, aside=0.0):
    extra_data = {T1: {"z": z}}
    if extra:
        for name, rots in extra.items():
            if name == T1:
                merged = {"z": z}
                merged.update(rots)
                extra_data[T1] = merged
            else:
                extra_data[name] = rots
    data = {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra_data,
    }
    if i_spread is not None:
        data["index"]["spread"] = i_spread
    return data


CASES = {
    "00_z30_i55": pose(0.55),
    "01_z30_i62": pose(0.62),
    "02_z30_i70": pose(0.70),
    "03_z30_i78": pose(0.78),
    "04_z30_i85": pose(0.85),
    "05_z26_i70": pose(0.70, z=26),
    "06_z34_i70": pose(0.70, z=34),
    "07_z38_i70": pose(0.70, z=38),
    "08_c08_i70": pose(0.70, t_curl=0.08),
    "09_c12_i70": pose(0.70, t_curl=0.12),
    "10_z30_i70_s8": pose(0.70, i_spread=8),
    "11_z30_i70_s-8": pose(0.70, i_spread=-8),
    "12_i2x12": pose(0.68, extra={I2: {"x": 12}}),
    "13_i2x-12": pose(0.68, extra={I2: {"x": -12}}),
    "14_t3z20": pose(0.70, extra={T3: {"z": 20}}),
    "15_t3z-20": pose(0.70, extra={T3: {"z": -20}}),
    "16_z32_i74_s6": pose(0.74, z=32, i_spread=6),
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

        def cam(orbit):
            page.evaluate(
                """(orbit) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = orbit;
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }""",
                orbit,
            )
            time.sleep(0.14)

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
                f"tip={m['distTip']:.4f} up={m['thumbUp']:.3f} horiz={m['thumbHoriz']:.3f} "
                f"dx={m['dx']:+.3f} dy={m['dy']:+.3f} dz={m['dz']:+.3f}"
            )
            cam("8deg 78deg 0.50m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-40deg 80deg 0.55m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        print("vertical + contact (up>0.90 first):")
        scored = sorted(
            ranked,
            key=lambda x: (
                0 if x[1]["thumbUp"] >= 0.90 else 1,
                (1 - max(0.0, x[1]["thumbUp"])) * 0.08 + x[1]["distNearest"],
            ),
        )
        for name, m in scored[:10]:
            print(
                f"  {name}: near={m['distNearest']:.4f} up={m['thumbUp']:.3f} horiz={m['thumbHoriz']:.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
