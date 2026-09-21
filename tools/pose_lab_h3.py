"""H lab 3: y180 + pulgar vertical + indice/medio juntos + dorso visible."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_h3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=h3"

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
  function dir(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    const len = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1;
    return { up: dy/len, x: dx/len, z: dz/len };
  }
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const thumb = dir(t1, t4);
  const index = dir(i1, i4);
  return {
    thumbUp: thumb.up, thumbX: thumb.x,
    indexX: index.x, indexUp: index.up,
    together: Math.hypot(i4.x-m4.x, i4.y-m4.y, i4.z-m4.z)
  };
}
"""


def pose(muneca, tz=-30, ispread=6, mspread=-6):
    return {
        "thumb": {"curl": 0.0},
        "index": {"curl": 0.0, "spread": ispread},
        "middle": {"curl": 0.0, "spread": mspread},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "muneca": muneca,
        "extra": {T1: {"z": tz}},
    }


CASES = {
    "00_y180": pose({"z": 90, "y": 180}),
    "01_y180_t-40": pose({"z": 90, "y": 180}, tz=-40),
    "02_y180_x25": pose({"z": 90, "y": 180, "x": 25}),
    "03_y180_x-25": pose({"z": 90, "y": 180, "x": -25}),
    "04_y180_x40": pose({"z": 90, "y": 180, "x": 40}),
    "05_y160": pose({"z": 90, "y": 160}),
    "06_y200": pose({"z": 90, "y": 200}),
    "07_y180_z80": pose({"z": 80, "y": 180}),
    "08_y180_z100": pose({"z": 100, "y": 180}),
    "09_y180_t-35": pose({"z": 90, "y": 180}, tz=-35),
    "10_y180_spread8": pose({"z": 90, "y": 180}, ispread=8, mspread=-8),
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
        time.sleep(8)
        for _ in range(50):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)
        time.sleep(1.5)

        # Warm-up pose so rest is settled before capturing.
        page.evaluate(
            "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
            pose({"z": 90, "y": 180}),
        )
        time.sleep(0.4)

        viewer = page.query_selector("#viewer")
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name}: thumbUp={m['thumbUp']:+.3f} idxX={m['indexX']:+.3f} "
                f"idxUp={m['indexUp']:+.3f} tog={m['together']:.4f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.08m 2.36m 0.20m';
                    mv.cameraOrbit = '20deg 78deg 0.55m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '-15deg 82deg 0.58m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        browser.close()


if __name__ == "__main__":
    main()
