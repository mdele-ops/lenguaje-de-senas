"""Afina el 04: brazo al frente y C de perfil visible."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_arm3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=carm3"

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
    "04_base": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 45}}},
    "a_fx30": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 30}}},
    "b_fx20": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 20}}},
    "c_fy20": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 40, "y": 20}}},
    "d_fym20": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 40, "y": -20}}},
    "e_fz20": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 40, "z": 20}}},
    "f_fzm20": {**F, "extra": {ARM: {"z": -20}, FORE: {"x": 40, "z": -20}}},
    "g_az-15_ay10_fx35": {
        **F,
        "extra": {ARM: {"z": -15, "y": 10}, FORE: {"x": 35}},
    },
    "h_az-25_fx40": {**F, "extra": {ARM: {"z": -25}, FORE: {"x": 40}}},
    "i_az-20_ay15_fx35_fy15": {
        **F,
        "extra": {ARM: {"z": -20, "y": 15}, FORE: {"x": 35, "y": 15}},
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
