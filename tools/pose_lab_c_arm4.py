"""Parte de b (muneca recta, C formada) y gira el brazo para ver el hueco."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_arm4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=carm4"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"

F = {
    "thumb": {"curl": 0.32, "aside": 0.42},
    "index": {"curl": 0.4, "spread": 18},
    "middle": {"curl": 0.4, "spread": 6},
    "ring": {"curl": 0.4, "spread": -14},
    "pinky": {"curl": 0.4, "spread": -24},
}

CASES = {
    "b_base": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 20}}},
    "ay12": {**F, "extra": {ARM: {"z": -20, "y": 12}, FORE: {"x": 20}}},
    "ay20": {**F, "extra": {ARM: {"z": -20, "y": 20}, FORE: {"x": 20}}},
    "aym12": {**F, "extra": {ARM: {"z": -20, "y": -12}, FORE: {"x": 20}}},
    "aym20": {**F, "extra": {ARM: {"z": -20, "y": -20}, FORE: {"x": 20}}},
    "fx25": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 25}}},
    "ay12_fx25": {**F, "extra": {ARM: {"z": -20, "y": 12}, FORE: {"x": 25}}},
    "az-16_ay10_fx22": {
        **F,
        "extra": {ARM: {"z": -16, "y": 10}, FORE: {"x": 22}},
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
            time.sleep(0.3)
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
