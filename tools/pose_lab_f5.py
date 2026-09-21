"""F: parte de 09 (pulgar vertical) y baja el indice a media altura."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f5"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f5"

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
  const idx = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t2 || !t3 || !t4 || !idx) return { error: 'bones' };
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const tdx = t4.x-t1.x, tdy = t4.y-t1.y, tdz = t4.z-t1.z;
  const tlen = Math.sqrt(tdx*tdx+tdy*tdy+tdz*tdz) || 1;
  const dx = idx.x-mid.x, dy = idx.y-mid.y, dz = idx.z-mid.z;
  return {
    dist: Math.sqrt(dx*dx+dy*dy+dz*dz), dx, dy, dz,
    thumbUp: tdy/tlen
  };
}
"""


def pose(i_curl, extra=None, t_curl=0.74, aside=-0.5, t1y=-60):
    data = {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": -2},
        "ring": {"curl": 0.0, "spread": -3},
        "pinky": {"curl": 0.0, "spread": -5},
        "extra": {T1: {"y": t1y}},
    }
    if extra:
        data["extra"].update(extra)
    return data


CASES = {
    "00_09": pose(0.78),
    "01_c80": pose(0.80),
    "02_c82": pose(0.82),
    "03_c84": pose(0.84),
    "04_c86": pose(0.86),
    "05_c82_i2": pose(0.80, {I2: {"x": 10}}),
    "06_c80_i3": pose(0.78, {I3: {"x": 12}}),
    "07_c82_y-65": pose(0.82, t1y=-65),
    "08_c82_y-55": pose(0.82, t1y=-55),
    "09_c82_t70": pose(0.82, t_curl=0.70),
    "10_c82_t80": pose(0.82, t_curl=0.80),
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

        print("closest:")
        for name, m in sorted(ranked, key=lambda x: x[1]["dist"])[:6]:
            print(f"  {name}: dist={m['dist']:.4f} up={m['thumbUp']:.3f}")
        browser.close()


if __name__ == "__main__":
    main()
