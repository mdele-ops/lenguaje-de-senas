"""Segunda pasada muneca C: enderezar linea antebrazo-mano (valores mayores)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_wrist2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=cwrist2"

HAND = "mixamorig1RightHand_035"
FORE = "mixamorig1RightForeArm_034"

FINGERS = {
    "thumb": {"curl": 0.32, "aside": 0.42},
    "index": {"curl": 0.4, "spread": 18},
    "middle": {"curl": 0.4, "spread": 6},
    "ring": {"curl": 0.4, "spread": -14},
    "pinky": {"curl": 0.4, "spread": -24},
}

CASES = {
    "00_actual": {**FINGERS, "muneca": {"y": -55}},
    "01_recta": {**FINGERS},
    "02_x40": {**FINGERS, "muneca": {"x": 40}},
    "03_x60": {**FINGERS, "muneca": {"x": 60}},
    "04_x80": {**FINGERS, "muneca": {"x": 80}},
    "05_xm40": {**FINGERS, "muneca": {"x": -40}},
    "06_z30": {**FINGERS, "muneca": {"z": 30}},
    "07_zm30": {**FINGERS, "muneca": {"z": -30}},
    "08_x50_z-15": {**FINGERS, "muneca": {"x": 50, "z": -15}},
    "09_fore_y30": {**FINGERS, "extra": {FORE: {"y": 30}}},
    "10_fore_ym30": {**FINGERS, "extra": {FORE: {"y": -30}}},
    "11_fore_z20": {**FINGERS, "extra": {FORE: {"z": 20}}},
    "12_x55_fore_y20": {
        **FINGERS,
        "muneca": {"x": 55},
        "extra": {FORE: {"y": 20}},
    },
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]
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

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.22)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_full.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.22m 2.28m 0.18m';
                    mv.cameraOrbit = '18deg 82deg 0.90m';
                    mv.fieldOfView = '22deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.3)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_wrist.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.45m 0.15m';
                    mv.cameraOrbit = '0deg 84deg 2.5m';
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.15)
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
