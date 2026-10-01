"""Candidatos: sacar el codo del torso (z- en el brazo)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=C&v=cout"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"
T1 = "mixamorig1RightHandThumb1_036"

FINGERS = {
    "thumb": {"curl": 0.32, "aside": 0.74},
    "index": {"curl": 0.4, "spread": -4},
    "middle": {"curl": 0.4, "spread": 3},
    "ring": {"curl": 0.4, "spread": 4},
    "pinky": {"curl": 0.4, "spread": 6},
}
HAND = {I1: {"x": 12}, M1: {"x": 12}, R1: {"x": 12}, P1: {"x": 12}, T1: {"y": 20}}


def pose(arm=None, fore=None):
    extra = dict(HAND)
    if arm:
        extra[ARM] = arm
    if fore:
        extra[FORE] = fore
    return {**FINGERS, "extra": extra}


CASES = {
    "00_reposo": pose(),
    "01_z-20": pose(arm={"z": -20}),
    "02_z-16_y12": pose(arm={"z": -16, "y": 12}),
    "03_z-20_y16": pose(arm={"z": -20, "y": 16}),
    "04_z-22_x-10": pose(arm={"z": -22, "x": -10}),
    "05_z-18_y10_fx8": pose(arm={"z": -18, "y": 10}, fore={"x": 8}),
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
        time.sleep(2.2)

        viewer = page.query_selector("#viewer")

        def cam(orbit):
            page.evaluate(
                """(orbit) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.42m 0.12m';
                    mv.cameraOrbit = orbit;
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }""",
                orbit,
            )
            time.sleep(0.22)

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            hand = page.evaluate(
                "() => window.__LSM_CONTROLLER__.getBoneWorld('mixamorig1RightHand_035')"
            )
            print(name, "hand", hand)
            cam("0deg 84deg 2.5m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("32deg 84deg 2.45m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))

        browser.close()


if __name__ == "__main__":
    main()
