"""Barre ejes del pulgar (curl 0) para encontrar la rotacion que lo pone vertical."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f15"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f15ax"

T1 = "mixamorig1RightHandThumb1_036"

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
  if (!t1 || !t4) return { error: 'bones' };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  return {
    thumbUp: tdy / tlen,
    thumbHoriz: Math.sqrt(tdx*tdx + tdz*tdz) / tlen,
    dir: { x: tdx/tlen, y: tdy/tlen, z: tdz/tlen }
  };
}
"""


def pose(extra=None):
    data = {
        "thumb": {"curl": 0.0, "aside": 0.0},
        "index": {"curl": 0.55},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
    }
    if extra:
        data["extra"] = extra
    return data


CASES = {"00_rest": pose()}
for axis in ("x", "y", "z"):
    for ang in (-90, -60, -30, 30, 60, 90):
        sign = "m" if ang < 0 else "p"
        CASES[f"{axis}_{sign}{abs(ang)}"] = pose({T1: {axis: ang}})


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

        def cam():
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

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.18)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            print(
                f"{name}: up={m['thumbUp']:+.3f} horiz={m['thumbHoriz']:.3f} "
                f"dir=({m['dir']['x']:+.2f},{m['dir']['y']:+.2f},{m['dir']['z']:+.2f})"
            )
            cam()
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))

        print("most vertical:")
        for name, m in sorted(ranked, key=lambda x: -x[1]["thumbUp"])[:8]:
            print(f"  {name}: up={m['thumbUp']:+.3f} horiz={m['thumbHoriz']:.3f}")
        browser.close()


if __name__ == "__main__":
    main()
