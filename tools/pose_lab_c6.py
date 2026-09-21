"""Letra C desde la B + giro a perfil para ver el arco de frente."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c6"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=c6"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
HAND = "mixamorig1RightHand_035"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"
T1 = "mixamorig1RightHandThumb1_036"

# Dedos juntos como la B, sin el solape de 18/-24
SHAPE = {
    "thumb": {"curl": 0.46, "aside": 0.58},
    "index": {"curl": 0.18, "spread": -4},
    "middle": {"curl": 0.18, "spread": 3},
    "ring": {"curl": 0.18, "spread": 4},
    "pinky": {"curl": 0.18, "spread": 6},
}
KNUCKLE = {I1: {"x": 28}, M1: {"x": 28}, R1: {"x": 28}, P1: {"x": 28}}


def extra(**bones):
    out = dict(KNUCKLE)
    out.update(bones)
    return out


CASES = {
    "00_actual": {
        "thumb": {"curl": 0.32, "aside": 0.42},
        "index": {"curl": 0.4, "spread": 18},
        "middle": {"curl": 0.4, "spread": 6},
        "ring": {"curl": 0.4, "spread": -14},
        "pinky": {"curl": 0.4, "spread": -24},
        "extra": {ARM: {"z": -20, "y": -12}, FORE: {"x": 20}},
    },
    "01_shape_only": {**SHAPE, "extra": extra()},
    "02_old_orient": {
        **SHAPE,
        "extra": extra(**{ARM: {"z": -20, "y": -12}, FORE: {"x": 20}}),
    },
    "03_my25": {**SHAPE, "muneca": {"y": 25}, "extra": extra()},
    "04_my-25": {**SHAPE, "muneca": {"y": -25}, "extra": extra()},
    "05_my-40": {**SHAPE, "muneca": {"y": -40}, "extra": extra()},
    "06_mz30": {**SHAPE, "muneca": {"z": 30}, "extra": extra()},
    "07_mz-30": {**SHAPE, "muneca": {"z": -30}, "extra": extra()},
    "08_mx20": {**SHAPE, "muneca": {"x": 20}, "extra": extra()},
    "09_fy40": {**SHAPE, "extra": extra(**{FORE: {"y": 40}})},
    "10_fy-40": {**SHAPE, "extra": extra(**{FORE: {"y": -40}})},
    "11_ay-25_fx20": {
        **SHAPE,
        "extra": extra(**{ARM: {"z": -18, "y": -25}, FORE: {"x": 20}}),
    },
    "12_ay-35_fx28": {
        **SHAPE,
        "extra": extra(**{ARM: {"z": -22, "y": -35}, FORE: {"x": 28}}),
    },
    "13_ay12_fx20_my-20": {
        **SHAPE,
        "muneca": {"y": -20},
        "extra": extra(**{ARM: {"z": -20, "y": 12}, FORE: {"x": 20}}),
    },
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
        time.sleep(6)
        for _ in range(50):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)

        viewer = page.query_selector("#viewer")

        def cam(target, orbit, fov):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.25)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.2)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_full.png"))
            cam("-0.26m 2.38m 0.22m", "12deg 78deg 0.58m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
