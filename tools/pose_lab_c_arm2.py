"""Sube el brazo y gira el antebrazo para mostrar la C de perfil."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_arm2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=carm2"

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
    "00_actual": {**F},
    "01_fx45": {**F, "extra": {FORE: {"x": 45}}},
    "02_fx60": {**F, "extra": {FORE: {"x": 60}}},
    "03_armz20_fx45": {**F, "extra": {ARM: {"z": 20}, FORE: {"x": 45}}},
    "04_armzm20_fx45": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 45}}},
    "05_army20_fx45": {**F, "extra": {ARM: {"y": 20}, FORE: {"x": 45}}},
    "06_armym20_fx45": {**F, "extra": {ARM: {"y": -20}, FORE: {"x": 45}}},
    "07_armx15_fx45": {**F, "extra": {ARM: {"x": 15}, FORE: {"x": 45}}},
    "08_armxm15_fx45": {**F, "extra": {ARM: {"x": -15}, FORE: {"x": 45}}},
    "09_armz25_fx55": {**F, "extra": {ARM: {"z": 25}, FORE: {"x": 55}}},
    "10_armz-25_fx55": {**F, "extra": {ARM: {"z": -25}, FORE: {"x": 55}}},
    "11_armz20_fy20_fx40": {
        **F,
        "extra": {ARM: {"z": 20}, FORE: {"x": 40, "y": 20}},
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
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
