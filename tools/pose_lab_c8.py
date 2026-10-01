"""Afina la C ganadora: perfil + arco suave + pulgar abajo del hueco."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c8"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=c8"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
T1 = "mixamorig1RightHandThumb1_036"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}
# Perfil que en c7 se leia como C de frente
PROFILE = {ARM: {"z": -22, "y": -38}, FORE: {"x": 26, "y": -18}}


def pose(curl, thumb_curl, thumb_aside, thumb_y=0, knuckle=0):
    extra = dict(PROFILE)
    if thumb_y:
        extra[T1] = {"y": thumb_y}
    if knuckle:
        extra[I1] = {"x": knuckle}
        extra[M1] = {"x": knuckle}
        extra[R1] = {"x": knuckle}
        extra[P1] = {"x": knuckle}
    return {
        "thumb": {"curl": thumb_curl, "aside": thumb_aside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
        "extra": extra,
    }


CASES = {
    "00_c7_02": pose(0.42, 0.34, 0.72),
    "01_c7_10": pose(0.36, 0.28, 0.80, thumb_y=28),
    "02_c40_t32_y22": pose(0.40, 0.32, 0.74, thumb_y=22),
    "03_c38_t30_y26": pose(0.38, 0.30, 0.76, thumb_y=26),
    "04_c44_t34_y18": pose(0.44, 0.34, 0.70, thumb_y=18),
    "05_c40_k12": pose(0.40, 0.32, 0.74, thumb_y=20, knuckle=12),
    "06_c36_k18": pose(0.36, 0.30, 0.76, thumb_y=24, knuckle=18),
    "07_c42_t28_aside82": pose(0.42, 0.28, 0.82, thumb_y=20),
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
            time.sleep(0.22)

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                data,
            )
            time.sleep(0.2)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_full.png"))
            cam("-0.20m 2.40m 0.16m", "6deg 80deg 0.95m", "22deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
