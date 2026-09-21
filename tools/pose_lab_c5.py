"""Candidatos letra C: arco abierto (no garra), dedos juntos sin solaparse."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c5"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=c5"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"
T1 = "mixamorig1RightHandThumb1_036"

# Junta de la B: juntos, sin cruzarse
JUNTA_B = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}
ORIENT = {ARM: {"z": -20, "y": -12}, FORE: {"x": 20}}


def fingers(curl, junta, thumb_curl=0.42, thumb_aside=0.55):
    return {
        "thumb": {"curl": thumb_curl, "aside": thumb_aside},
        "index": {"curl": curl, "spread": junta["index"]},
        "middle": {"curl": curl, "spread": junta["middle"]},
        "ring": {"curl": curl, "spread": junta["ring"]},
        "pinky": {"curl": curl, "spread": junta["pinky"]},
    }


def knuckle(deg=26):
    return {I1: {"x": deg}, M1: {"x": deg}, R1: {"x": deg}, P1: {"x": deg}}


CASES = {
    "00_actual": {
        "thumb": {"curl": 0.32, "aside": 0.42},
        "index": {"curl": 0.4, "spread": 18},
        "middle": {"curl": 0.4, "spread": 6},
        "ring": {"curl": 0.4, "spread": -14},
        "pinky": {"curl": 0.4, "spread": -24},
        "extra": ORIENT,
    },
    "01_juntaB_c28": {**fingers(0.28, JUNTA_B), "extra": {**ORIENT}},
    "02_juntaB_c34": {**fingers(0.34, JUNTA_B), "extra": {**ORIENT}},
    "03_knuckle_c16": {
        **fingers(0.16, JUNTA_B, 0.46, 0.58),
        "extra": {**ORIENT, **knuckle(28)},
    },
    "04_knuckle_c20": {
        **fingers(0.20, JUNTA_B, 0.48, 0.6),
        "extra": {**ORIENT, **knuckle(22)},
    },
    "05_open_c22": {**fingers(0.22, JUNTA_B, 0.4, 0.65), "extra": {**ORIENT}},
    "06_thumb_up": {
        **fingers(0.26, JUNTA_B, 0.52, 0.7),
        "extra": {**ORIENT, T1: {"y": 25}},
    },
    "07_no_arm": {**fingers(0.28, JUNTA_B, 0.46, 0.58)},
    "08_knuckle_thumb": {
        **fingers(0.15, JUNTA_B, 0.5, 0.62),
        "extra": {**ORIENT, **knuckle(30), T1: {"y": 20}},
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
            time.sleep(0.28)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.22)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_full.png"))
            cam("-0.28m 2.36m 0.20m", "10deg 78deg 0.52m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.28m 2.36m 0.20m", "-50deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
