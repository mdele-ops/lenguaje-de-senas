"""Afina la muneca de la C: menos torsion, linea natural antebrazo-mano."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_wrist"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=cwrist"

FINGERS = {
    "thumb": {"curl": 0.32, "aside": 0.42},
    "index": {"curl": 0.4, "spread": 18},
    "middle": {"curl": 0.4, "spread": 6},
    "ring": {"curl": 0.4, "spread": -14},
    "pinky": {"curl": 0.4, "spread": -24},
}

CASES = {
    "00_actual_y-55": {**FINGERS, "muneca": {"y": -55}},
    "01_sin_muneca": {**FINGERS},
    "02_y-15": {**FINGERS, "muneca": {"y": -15}},
    "03_y-25": {**FINGERS, "muneca": {"y": -25}},
    "04_y-35": {**FINGERS, "muneca": {"y": -35}},
    "05_z-15": {**FINGERS, "muneca": {"z": -15}},
    "06_z15": {**FINGERS, "muneca": {"z": 15}},
    "07_x-15": {**FINGERS, "muneca": {"x": -15}},
    "08_x15": {**FINGERS, "muneca": {"x": 15}},
    "09_y-20_z-8": {**FINGERS, "muneca": {"y": -20, "z": -8}},
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
                    mv.cameraTarget = '-0.22m 2.28m 0.18m';
                    mv.cameraOrbit = '12deg 82deg 0.85m';
                    mv.fieldOfView = '22deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.35)
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
            time.sleep(0.2)
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
