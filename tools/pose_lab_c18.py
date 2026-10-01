"""C18: mas de lado + muneca atras, C de indice+pulgar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c18"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c18"

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
    "a_y50_z45": pose({"y": 50, "z": 45}),
    "b_y70_z40": pose({"y": 70, "z": 40}),
    "c_y80_z35": pose({"y": 80, "z": 35}),
    "d_y75_z50": pose({"y": 75, "z": 50}),
    "e_y85_z40": pose({"y": 85, "z": 40}),
    "f_y70_z55": pose({"y": 70, "z": 55}),
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

        for name, data in CASES.items():
            page.evaluate("(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data)
            time.sleep(0.25)
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.45m 0.15m';
                    mv.cameraOrbit = '0deg 84deg 2.5m';
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.2)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
