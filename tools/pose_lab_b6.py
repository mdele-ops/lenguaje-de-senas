"""Captura los candidatos con pulgar mas hacia arriba (segun medicion dy)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_b6"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=b6c"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

F = {
    "index": {"curl": 0.0, "spread": 14},
    "middle": {"curl": 0.0, "spread": 4},
    "ring": {"curl": 0.0, "spread": -10},
    "pinky": {"curl": 0.0, "spread": -20},
}

CASES = {
    "00_actual": {**F, "thumb": {"curl": 0.74, "aside": -0.5}},
    "01_t1y-60": {**F, "thumb": {"curl": 0.74, "aside": -0.5}, "extra": {T1: {"y": -60}}},
    "02_t1y-90": {**F, "thumb": {"curl": 0.74, "aside": -0.5}, "extra": {T1: {"y": -90}}},
    "03_t1y-75": {**F, "thumb": {"curl": 0.74, "aside": -0.5}, "extra": {T1: {"y": -75}}},
    "04_curl02": {**F, "thumb": {"curl": 0.2, "aside": -0.5}},
    "05_curl02_y-50": {**F, "thumb": {"curl": 0.2, "aside": -0.5}, "extra": {T1: {"y": -50}}},
    "06_curl015_y-55": {**F, "thumb": {"curl": 0.15, "aside": -0.35}, "extra": {T1: {"y": -55}}},
    "07_t2x-60": {**F, "thumb": {"curl": 0.74, "aside": -0.5}, "extra": {T2: {"x": -60}}},
    "08_curl03_y-45": {**F, "thumb": {"curl": 0.3, "aside": -0.4}, "extra": {T1: {"y": -45}}},
    "09_curl01_y-70": {**F, "thumb": {"curl": 0.1, "aside": -0.25}, "extra": {T1: {"y": -70}}},
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]
        )
        page = browser.new_page(viewport={"width": 800, "height": 800})
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
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '8deg 78deg 0.50m';
                mv.fieldOfView = '18deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.4)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.3)
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
