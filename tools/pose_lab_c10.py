"""Afina la C ganadora: muneca y+ y arco mas abierto, como la referencia."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c10"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c10"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
T1 = "mixamorig1RightHandThumb1_036"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}


def pose(curl, thumb_curl, thumb_aside, thumb_y=20, knuckle=12, muneca=None, arm=None):
    extra = {
        I1: {"x": knuckle},
        M1: {"x": knuckle},
        R1: {"x": knuckle},
        P1: {"x": knuckle},
        T1: {"y": thumb_y},
    }
    if arm:
        extra[ARM] = arm
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


# Base ganadora de c9: arm z-18 + muneca y 50
CASES = {
    "00_c9_02": pose(0.40, 0.32, 0.74, muneca={"y": 50}, arm={"z": -18}),
    "01_open28": pose(0.28, 0.28, 0.78, muneca={"y": 50}, arm={"z": -18}),
    "02_open32": pose(0.32, 0.28, 0.78, muneca={"y": 50}, arm={"z": -18}),
    "03_open36": pose(0.36, 0.30, 0.76, muneca={"y": 50}, arm={"z": -18}),
    "04_my45": pose(0.32, 0.28, 0.78, muneca={"y": 45}, arm={"z": -18}),
    "05_my58": pose(0.32, 0.28, 0.78, muneca={"y": 58}, arm={"z": -18}),
    "06_my50_mz12": pose(0.32, 0.28, 0.78, muneca={"y": 50, "z": 12}, arm={"z": -18}),
    "07_my50_mz-12": pose(0.32, 0.28, 0.78, muneca={"y": 50, "z": -12}, arm={"z": -18}),
    "08_k18_c30": pose(0.30, 0.26, 0.80, knuckle=18, muneca={"y": 52}, arm={"z": -18}),
    "09_thumbup": pose(0.32, 0.22, 0.82, thumb_y=28, muneca={"y": 50}, arm={"z": -18}),
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
        time.sleep(1.2)

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
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.22)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("0m 2.42m 0.12m", "22deg 84deg 2.4m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
