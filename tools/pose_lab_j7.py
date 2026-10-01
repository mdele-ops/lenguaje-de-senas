"""J lab 7: trazo tipo escritura (I + dibujar J), palma un poco de lado."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j7"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=j7"

T1 = "mixamorig1RightHandThumb1_036"
FINGERS = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.0},
    "extra": {T1: {"y": -60, "x": -12}},
}

# Secuencias candidatas: meñique empieza ARRIBA y dibuja J
SEQ_A = {
    "a0": {"x": 0, "y": 35, "z": 0},
    "a1": {"x": 28, "y": 38, "z": -8},
    "a2": {"x": 52, "y": 40, "z": -18},
    "a3": {"x": 48, "y": 28, "z": -48},
    "a4": {"x": 18, "y": 15, "z": -75},
}
SEQ_B = {
    "b0": {"x": 0, "y": 20, "z": 0},
    "b1": {"x": 25, "y": 20, "z": 12},
    "b2": {"x": 45, "y": 15, "z": 28},
    "b3": {"x": 40, "y": 5, "z": 55},
    "b4": {"x": 15, "y": -10, "z": 78},
}
SEQ_C = {
    "c0": {"x": 0, "y": 0, "z": 0},
    "c1": {"x": 20, "y": 0, "z": 18},
    "c2": {"x": 35, "y": 5, "z": 40},
    "c3": {"x": 28, "y": -8, "z": 68},
    "c4": {"x": 8, "y": -20, "z": 88},
}

CASES = {}
CASES.update(SEQ_A)
CASES.update(SEQ_B)
CASES.update(SEQ_C)


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
