"""C12: mezcla 08_thumbup + 05_abierta para igualar la foto LSM."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c12"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c12"

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"
JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}


def pose(curl, tcurl, taside, knuckle, ty, tz, t2x, my, armz=-18):
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
        "muneca": {"y": my},
        "extra": {
            I1: {"x": knuckle},
            M1: {"x": knuckle},
            R1: {"x": knuckle},
            P1: {"x": knuckle},
            T1: {"y": ty, "z": tz},
            T2: {"x": t2x},
            ARM: {"z": armz},
        },
    }


CASES = {
    "00_actual": pose(0.40, 0.32, 0.74, 12, 20, 0, 0, 50),
    "01_08": pose(0.40, 0.28, 0.78, 16, 28, 6, -8, 50),
    "02_05": pose(0.34, 0.30, 0.76, 22, 24, 8, -10, 54),
    "03_mix": pose(0.36, 0.28, 0.78, 20, 26, 8, -10, 54),
    "04_foto": pose(0.38, 0.26, 0.80, 18, 28, 6, -8, 52),
    "05_arco": pose(0.36, 0.30, 0.76, 22, 24, 10, -12, 50),
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
            time.sleep(0.2)

        for name, data in CASES.items():
            page.evaluate("(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data)
            time.sleep(0.22)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("-0.22m 2.38m 0.16m", "18deg 80deg 0.62m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_close.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
