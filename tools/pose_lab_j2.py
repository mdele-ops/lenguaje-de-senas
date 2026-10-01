"""J lab 2: candidatos de keyframes del trazo de muneca."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j2"

T1 = "mixamorig1RightHandThumb1_036"

FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
    "extra": {T1: {"y": -60, "x": -12}},
}


def pose(muneca):
    data = dict(FINGERS)
    data["muneca"] = muneca
    return data


CASES = {
    "k0_start": pose({"x": 0, "y": 0, "z": 0}),
    "k1_down_a": pose({"x": 30, "y": 0, "z": 12}),
    "k1_down_b": pose({"x": 40, "y": 5, "z": 20}),
    "k2_bottom_a": pose({"x": 50, "y": -10, "z": 40}),
    "k2_bottom_b": pose({"x": 45, "y": -20, "z": 50}),
    "k3_hook_a": pose({"x": 18, "y": -35, "z": 62}),
    "k3_hook_b": pose({"x": 10, "y": -45, "z": 70}),
    "k3_hook_c": pose({"x": 25, "y": -55, "z": 55}),
    "alt_yhook": pose({"x": 35, "y": -60, "z": 25}),
    "alt_xdown": pose({"x": 60, "y": -15, "z": 10}),
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
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.22)
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '-40deg 80deg 0.55m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_user.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.3m 2.3m 0.15m';
                    mv.cameraOrbit = '5deg 82deg 0.75m';
                    mv.fieldOfView = '25deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_rev.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.40m 0.15m';
                    mv.cameraOrbit = '18deg 84deg 2.4m';
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
