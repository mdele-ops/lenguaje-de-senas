"""C sin clipping: mide huesos y prueba brazos mas afuera."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_clear2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=cclear2"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
HAND = "mixamorig1RightHand_035"
T1 = "mixamorig1RightHandThumb1_036"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

SHAPE = {
    "thumb": {"curl": 0.32, "aside": 0.74},
    "index": {"curl": 0.4, "spread": -4},
    "middle": {"curl": 0.4, "spread": 3},
    "ring": {"curl": 0.4, "spread": 4},
    "pinky": {"curl": 0.4, "spread": 6},
}
HAND_EXTRA = {I1: {"x": 12}, M1: {"x": 12}, R1: {"x": 12}, P1: {"x": 12}, T1: {"y": 20}}


def extra(arm=None, fore=None, muneca=None):
    out = dict(HAND_EXTRA)
    if arm:
        out[ARM] = arm
    if fore:
        out[FORE] = fore
    pose = {**SHAPE, "extra": out}
    if muneca:
        pose["muneca"] = muneca
    return pose


CASES = {
    "00_actual": extra(arm={"z": -22, "y": -38}, fore={"x": 26, "y": -18}),
    "01_brazo_reposo": extra(),
    "02_suave_old": extra(arm={"z": -10, "y": -12}, fore={"x": 12}),
    "03_muy_suave": extra(arm={"z": -6, "y": -8}, fore={"x": 8}),
    "04_muneca_y-40": extra(muneca={"y": -40}),
    "05_muneca_y40": extra(muneca={"y": 40}),
    "06_ay-10_az8": extra(arm={"y": -10, "z": 8}, fore={"x": 10}),
    "07_az18": extra(arm={"z": 18}),
    "08_az24_ax8": extra(arm={"z": 24, "x": 8}),
    "09_ax20": extra(arm={"x": 20}),
    "10_ax-20": extra(arm={"x": -20}),
    "11_az20_ay8": extra(arm={"z": 20, "y": 8}),
}

MEASURE_JS = """() => {
  const mv = document.getElementById('handViewer');
  const scene = mv.model && mv.model.scene;
  if (!scene) return null;
  const names = [
    'mixamorig1Spine2_03',
    'mixamorig1RightArm_033',
    'mixamorig1RightForeArm_034',
    'mixamorig1RightHand_035',
  ];
  const out = {};
  names.forEach((name) => {
    let found = null;
    scene.traverse((o) => { if (o.name === name) found = o; });
    if (!found) { out[name] = null; return; }
    found.updateWorldMatrix(true, false);
    const e = found.matrixWorld.elements;
    out[name] = {
      x: +e[12].toFixed(3),
      y: +e[13].toFixed(3),
      z: +e[14].toFixed(3),
    };
  });
  return out;
}"""


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
        time.sleep(2.2)

        viewer = page.query_selector("#viewer")
        results = {}

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
            time.sleep(0.2)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.25)
            pos = page.evaluate(MEASURE_JS)
            results[name] = pos
            spine = (pos or {}).get("mixamorig1Spine2_03") or {}
            hand = (pos or {}).get("mixamorig1RightHand_035") or {}
            print(
                name,
                "hand",
                hand,
                "dx",
                round((hand.get("x", 0) - spine.get("x", 0)), 3),
                "dz",
                round((hand.get("z", 0) - spine.get("z", 0)), 3),
            )
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("0m 2.40m 0.10m", "70deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))

        (OUT_DIR / "positions.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        browser.close()


if __name__ == "__main__":
    main()
