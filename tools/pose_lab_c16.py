"""C16: doblar muneca atras — dedos de lado, C de indice+pulgar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c16"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c16"

ARM = "mixamorig1RightArm_033"
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


def pose(muneca):
    return {**FINGERS, "muneca": muneca, "extra": dict(HAND)}


CASES = {
    "00_actual": pose({"x": -45, "y": 50}),
    "01_y50": pose({"y": 50}),
    "02_y50_z30": pose({"y": 50, "z": 30}),
    "03_y50_z50": pose({"y": 50, "z": 50}),
    "04_y50_z70": pose({"y": 50, "z": 70}),
    "05_y50_zm30": pose({"y": 50, "z": -30}),
    "06_y50_zm50": pose({"y": 50, "z": -50}),
    "07_y50_x30": pose({"y": 50, "x": 30}),
    "08_y50_x50": pose({"y": 50, "x": 50}),
    "09_y50_x70": pose({"y": 50, "x": 70}),
    "10_y70_z40": pose({"y": 70, "z": 40}),
    "11_y90_z30": pose({"y": 90, "z": 30}),
    "12_y50_x40_z20": pose({"y": 50, "x": 40, "z": 20}),
    "13_y60_x35": pose({"y": 60, "x": 35}),
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
