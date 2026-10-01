"""Letra C: perfil visible de frente, brazo fuera del torso."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c9"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c9"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
T1 = "mixamorig1RightHandThumb1_036"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}
KNUCKLE = {I1: {"x": 12}, M1: {"x": 12}, R1: {"x": 12}, P1: {"x": 12}, T1: {"y": 20}}


def pose(curl=0.4, thumb_curl=0.32, thumb_aside=0.74, muneca=None, arm=None, fore=None):
    extra = dict(KNUCKLE)
    if arm:
        extra[ARM] = arm
    if fore:
        extra[FORE] = fore
    data = {
        "thumb": {"curl": thumb_curl, "aside": thumb_aside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
        "extra": extra,
    }
    if muneca:
        data["muneca"] = muneca
    return data


CASES = {
    "00_actual": pose(arm={"z": -20}),
    "01_my-50": pose(arm={"z": -18}, muneca={"y": -50}),
    "02_my50": pose(arm={"z": -18}, muneca={"y": 50}),
    "03_mz-45": pose(arm={"z": -18}, muneca={"z": -45}),
    "04_mz45": pose(arm={"z": -18}, muneca={"z": 45}),
    "05_fy-55": pose(arm={"z": -18}, fore={"y": -55, "x": 12}),
    "06_fy50": pose(arm={"z": -18}, fore={"y": 50, "x": 12}),
    "07_fy-40_my-30": pose(arm={"z": -18}, fore={"y": -40}, muneca={"y": -30}),
    "08_fy40_my30": pose(arm={"z": -18}, fore={"y": 40}, muneca={"y": 30}),
    "09_az-20_fy-45": pose(arm={"z": -20}, fore={"y": -45, "x": 10}),
    "10_az-20_fy45": pose(arm={"z": -20}, fore={"y": 45, "x": 10}),
    "11_az-16_mz-55": pose(arm={"z": -16}, muneca={"z": -55}),
    "12_az-16_mz55": pose(arm={"z": -16}, muneca={"z": 55}),
    "13_clip_old": pose(arm={"z": -22, "y": -38}, fore={"x": 26, "y": -18}),
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
        time.sleep(1.5)

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

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.25)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("-0.28m 2.36m 0.20m", "8deg 78deg 0.52m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
