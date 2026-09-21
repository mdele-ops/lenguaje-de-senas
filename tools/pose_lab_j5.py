"""J lab 5: palma de lado + barrido de z para dibujar la J."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j5"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j5"

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
    "k0_start": {"y": 80, "z": 0, "x": 0},
    "k1_down": {"y": 80, "z": 35, "x": 8},
    "k2_mid": {"y": 75, "z": 65, "x": 12},
    "k3_low": {"y": 65, "z": 90, "x": 10},
    "k4_hook": {"y": 45, "z": 100, "x": 18},
    "k5_end": {"y": 30, "z": 85, "x": 28},
    "b0": {"y": 90, "z": 0, "x": 0},
    "b1": {"y": 90, "z": 45, "x": 0},
    "b2": {"y": 90, "z": 80, "x": 5},
    "b3": {"y": 70, "z": 100, "x": 15},
    "b4": {"y": 40, "z": 95, "x": 30},
    "c0": {"z": 0},
    "c1": {"z": 40},
    "c2": {"z": 75},
    "c3": {"z": 100},
    "c4": {"z": 110, "y": -25},
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
        time.sleep(0.8)

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
