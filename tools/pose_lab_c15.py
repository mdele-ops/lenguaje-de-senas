"""C15: muneca vertical como la foto (C de perfil, hueco a un lado)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c15"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c15"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

FINGERS = {
    "thumb": {"curl": 0.24, "aside": 0.82},
    "index": {"curl": 0.46, "spread": -4},
    "middle": {"curl": 0.46, "spread": 3},
    "ring": {"curl": 0.46, "spread": 4},
    "pinky": {"curl": 0.46, "spread": 6},
}


def pose(muneca, fore=None, armz=-18):
    extra = {
        I1: {"x": 26},
        M1: {"x": 26},
        R1: {"x": 26},
        P1: {"x": 26},
        T1: {"y": 30, "z": 4},
        T2: {"x": -6},
        ARM: {"z": armz},
    }
    if fore:
        extra[FORE] = fore
    return {**FINGERS, "muneca": muneca, "extra": extra}


CASES = {
    "00_actual": pose({"y": 50, "z": 20}),
    "01_y50": pose({"y": 50}),
    "02_y50_xm20": pose({"y": 50, "x": -20}),
    "03_y50_xm35": pose({"y": 50, "x": -35}),
    "04_y50_xm50": pose({"y": 50, "x": -50}),
    "05_y50_xm70": pose({"y": 50, "x": -70}),
    "06_y40_xm40": pose({"y": 40, "x": -40}),
    "07_y70_xm40": pose({"y": 70, "x": -40}),
    "08_y50_xm40_z12": pose({"y": 50, "x": -40, "z": 12}),
    "09_y50_xm45_fx25": pose({"y": 50, "x": -45}, fore={"x": 25}),
    "10_y50_xm45_fx40": pose({"y": 50, "x": -45}, fore={"x": 40}),
    "11_ym50_xm40": pose({"y": -50, "x": -40}),
    "12_y55_xm55": pose({"y": 55, "x": -55}),
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
            time.sleep(0.22)

        for name, data in CASES.items():
            page.evaluate("(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data)
            time.sleep(0.22)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("-0.28m 2.32m 0.18m", "8deg 78deg 0.55m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
