"""Gira el antebrazo/brazo de la C para mostrar el perfil, sin romper la muneca."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_arm"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=carm"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"

FINGERS = {
    "thumb": {"curl": 0.32, "aside": 0.42},
    "index": {"curl": 0.4, "spread": 18},
    "middle": {"curl": 0.4, "spread": 6},
    "ring": {"curl": 0.4, "spread": -14},
    "pinky": {"curl": 0.4, "spread": -24},
}

CASES = {
    "00_actual": {**FINGERS},
    "01_fore_y40": {**FINGERS, "extra": {FORE: {"y": 40}}},
    "02_fore_y55": {**FINGERS, "extra": {FORE: {"y": 55}}},
    "03_fore_y70": {**FINGERS, "extra": {FORE: {"y": 70}}},
    "04_fore_ym40": {**FINGERS, "extra": {FORE: {"y": -40}}},
    "05_fore_ym55": {**FINGERS, "extra": {FORE: {"y": -55}}},
    "06_fore_z25": {**FINGERS, "extra": {FORE: {"z": 25}}},
    "07_fore_zm25": {**FINGERS, "extra": {FORE: {"z": -25}}},
    "08_fore_x30": {**FINGERS, "extra": {FORE: {"x": 30}}},
    "09_fore_xm30": {**FINGERS, "extra": {FORE: {"x": -30}}},
    "10_arm_y20_fore_y50": {
        **FINGERS,
        "extra": {ARM: {"y": 20}, FORE: {"y": 50}},
    },
    "11_arm_ym15_fore_ym50": {
        **FINGERS,
        "extra": {ARM: {"y": -15}, FORE: {"y": -50}},
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
            time.sleep(0.25)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_full.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.22m 2.32m 0.18m';
                    mv.cameraOrbit = '10deg 80deg 0.95m';
                    mv.fieldOfView = '22deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.3)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
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
