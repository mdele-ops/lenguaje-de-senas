"""Barrido de ejes del pulgar (pose.extra) para subirlo en la letra B."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_b4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?v=b4b"

THUMB1 = "mixamorig1RightHandThumb1_036"
THUMB2 = "mixamorig1RightHandThumb2_037"

FINGERS = {
    "thumb": {"curl": 0.0},
    "index": {"curl": 0.0, "spread": 14},
    "middle": {"curl": 0.0, "spread": 4},
    "ring": {"curl": 0.0, "spread": -10},
    "pinky": {"curl": 0.0, "spread": -20},
}

CASES = {"base": dict(FINGERS)}
for bone_key, bone_name in [("t1", THUMB1), ("t2", THUMB2)]:
    for axis in ("x", "y", "z"):
        for deg in (-45, -90, 45, 90):
            pose = dict(FINGERS)
            pose["extra"] = {bone_name: {axis: deg}}
            CASES[f"{bone_key}_{axis}{deg:+d}"] = pose


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
            ready = page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            )
            if ready:
                break
            time.sleep(0.3)

        viewer = page.query_selector("#viewer")
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '10deg 78deg 0.48m';
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
            time.sleep(0.28)
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
