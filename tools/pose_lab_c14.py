"""C14: solo muneca — misma C, mas visible de frente."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c14"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c14"

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
HAND = {
    I1: {"x": 26},
    M1: {"x": 26},
    R1: {"x": 26},
    P1: {"x": 26},
    T1: {"y": 30, "z": 4},
    T2: {"x": -6},
    ARM: {"z": -18},
}


def pose(muneca, fore=None):
    extra = dict(HAND)
    if fore:
        extra[FORE] = fore
    return {**FINGERS, "muneca": muneca, "extra": extra}


CASES = {
    "00_y50": pose({"y": 50}),
    "01_y70": pose({"y": 70}),
    "02_y90": pose({"y": 90}),
    "03_y50_z20": pose({"y": 50, "z": 20}),
    "04_y50_z-20": pose({"y": 50, "z": -20}),
    "05_y50_x20": pose({"y": 50, "x": 20}),
    "06_y50_x-20": pose({"y": 50, "x": -20}),
    "07_y65_z15": pose({"y": 65, "z": 15}),
    "08_y65_z-15": pose({"y": 65, "z": -15}),
    "09_y40_x-15": pose({"y": 40, "x": -15}),
    "10_y-50": pose({"y": -50}),
    "11_y-70": pose({"y": -70}),
    "12_y55_x-12_z12": pose({"y": 55, "x": -12, "z": 12}),
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
            time.sleep(0.2)

        for name, data in CASES.items():
            page.evaluate("(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data)
            time.sleep(0.22)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
