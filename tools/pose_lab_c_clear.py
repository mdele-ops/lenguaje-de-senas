"""Letra C: misma forma de mano, brazo fuera del torso."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_clear"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=cclear"

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
KNUCKLE = {I1: {"x": 12}, M1: {"x": 12}, R1: {"x": 12}, P1: {"x": 12}, T1: {"y": 20}}


def extra(arm=None, fore=None, hand=None, muneca=None):
    out = dict(KNUCKLE)
    if arm:
        out[ARM] = arm
    if fore:
        out[FORE] = fore
    if hand:
        out[HAND] = hand
    pose = {**SHAPE, "extra": out}
    if muneca:
        pose["muneca"] = muneca
    return pose


CASES = {
    "00_actual_clip": extra(arm={"z": -22, "y": -38}, fore={"x": 26, "y": -18}),
    "01_sin_brazo": extra(),
    "02_ay10": extra(arm={"y": 10}),
    "03_ay18": extra(arm={"y": 18}),
    "04_az12": extra(arm={"z": 12}),
    "05_az-12": extra(arm={"z": -12}),
    "06_ax-12": extra(arm={"x": -12}),
    "07_ax12": extra(arm={"x": 12}),
    "08_ay18_az10": extra(arm={"y": 18, "z": 10}),
    "09_ay22_fx16": extra(arm={"y": 22}, fore={"x": 16}),
    "10_ay20_fy-20": extra(arm={"y": 20}, fore={"y": -20}),
    "11_ay16_my-35": extra(arm={"y": 16}, muneca={"y": -35}),
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
        time.sleep(6)
        for _ in range(50):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)

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
            time.sleep(0.22)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.2)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("0m 2.45m 0.15m", "55deg 84deg 2.6m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
