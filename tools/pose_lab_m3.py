"""M lab 3: juntar los tres dedos y ver la pose con la camara de produccion."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_m3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=m3"

T1 = "mixamorig1RightHandThumb1_036"
ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"

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
  if (!scene) return { error: 'no-scene' };
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  function pos(name) {
    const b = bones[name];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  return {
    togIM: Math.hypot(i4.x - m4.x, i4.y - m4.y, i4.z - m4.z),
    togMR: Math.hypot(m4.x - r4.x, m4.y - r4.y, m4.z - r4.z),
  };
}
"""


def pose(spread=8, x=150, extra=None, curl=0.04):
    data = {
        "thumb": {"curl": 0.74, "aside": -0.5},
        "index": {"curl": curl, "spread": spread},
        "middle": {"curl": curl},
        "ring": {"curl": curl, "spread": -spread},
        "pinky": {"curl": 0.95},
        "muneca": {"x": x},
        "extra": {T1: {"y": -60, "x": -12}, ARM: {"z": -18}},
    }
    if extra:
        data["extra"].update(extra)
    return data


CASES = {
    "00_s8_x140": pose(spread=8, x=140),
    "01_s8_x150": pose(spread=8, x=150),
    "02_s16_x150": pose(spread=16, x=150),
    "03_s22_x150": pose(spread=22, x=150),
    "04_s16_x145": pose(spread=16, x=145),
    "05_s16_x155": pose(spread=16, x=155),
    "06_s16_arm24": pose(spread=16, x=150, extra={ARM: {"z": -24}}),
    "07_s16_fore": pose(spread=16, x=150, extra={FORE: {"x": 12}}),
    "08_align": pose(
        spread=16,
        x=150,
        extra={I1: {"z": 4}, R1: {"z": -4}},
    ),
    "09_s16_x148_arm20": pose(spread=16, x=148, extra={ARM: {"z": -20}}),
}


def set_cam(page, kind):
    if kind == "prod":
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '0m 2.45m 0.15m';
                mv.cameraOrbit = '0deg 84deg 2.5m';
                mv.fieldOfView = '30deg';
                mv.jumpCameraToGoal();
            }"""
        )
    elif kind == "wide":
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.18m 2.20m 0.18m';
                mv.cameraOrbit = '22deg 78deg 1.15m';
                mv.fieldOfView = '22deg';
                mv.jumpCameraToGoal();
            }"""
        )
    else:
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.22m 2.14m 0.22m';
                mv.cameraOrbit = '-6deg 80deg 0.80m';
                mv.fieldOfView = '20deg';
                mv.jumpCameraToGoal();
            }"""
        )


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
        ready = False
        for _ in range(80):
            try:
                if page.evaluate(
                    "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
                ):
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.3)
        if not ready:
            raise RuntimeError("El modelo 3D no cargo a tiempo")
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")
        page.evaluate(
            "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
            pose(),
        )
        time.sleep(0.4)

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.22)
            m = page.evaluate(MEASURE_JS)
            print(f"{name:20s}  togIM={m['togIM']:.4f} togMR={m['togMR']:.4f}")

            set_cam(page, "prod")
            time.sleep(0.10)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_prod.png"))
            set_cam(page, "wide")
            time.sleep(0.10)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_wide.png"))
            set_cam(page, "front")
            time.sleep(0.10)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        browser.close()


if __name__ == "__main__":
    main()
