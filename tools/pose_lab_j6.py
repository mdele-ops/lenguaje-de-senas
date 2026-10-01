"""J lab 6: palma de lado y barrido hacia el pulgar (z negativo)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j6"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j6"

T1 = "mixamorig1RightHandThumb1_036"
FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
    "extra": {T1: {"y": -60, "x": -12}},
}

CASES = {
    "d0": {"y": 90, "z": 0, "x": 0},
    "d1": {"y": 90, "z": -40, "x": 5},
    "d2": {"y": 85, "z": -70, "x": 10},
    "d3": {"y": 70, "z": -95, "x": 18},
    "d4": {"y": 45, "z": -105, "x": 28},
    "e0": {"y": 90, "z": 0, "x": 0},
    "e1": {"y": 80, "z": 30, "x": 10},
    "e2": {"y": 55, "z": 70, "x": 20},
    "e3": {"y": 25, "z": 95, "x": 25},
    "e4": {"y": 5, "z": 85, "x": 40},
}


def pose(muneca):
    data = dict(FINGERS)
    data["muneca"] = muneca
    return data


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

        viewer = page.query_selector("#viewer")
        for name, muneca in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", pose(muneca)
            )
            time.sleep(0.18)
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.40m 0.15m';
                    mv.cameraOrbit = '12deg 84deg 2.3m';
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
