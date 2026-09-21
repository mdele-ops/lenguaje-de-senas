"""C19: pulgar y dedos como la foto — arco C abierto, no garra."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c19"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c19fingers"

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"
I1 = "mixamorig1RightHandIndex1_040"
I2 = "mixamorig1RightHandIndex2_041"
M1 = "mixamorig1RightHandMiddle1_044"
M2 = "mixamorig1RightHandMiddle2_045"
R1 = "mixamorig1RightHandRing1_048"
R2 = "mixamorig1RightHandRing2_049"
P1 = "mixamorig1RightHandPinky1_052"
P2 = "mixamorig1RightHandPinky2_053"

JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}


def fingers(curl, thumb_curl, thumb_aside):
    return {
        "thumb": {"curl": thumb_curl, "aside": thumb_aside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
    }


def knuckles(deg, mid=0):
    extra = {
        I1: {"x": deg},
        M1: {"x": deg},
        R1: {"x": deg},
        P1: {"x": deg},
        ARM: {"z": -18},
    }
    if mid:
        extra[I2] = {"x": mid}
        extra[M2] = {"x": mid}
        extra[R2] = {"x": mid}
        extra[P2] = {"x": mid}
    return extra


def pose(curl, tcurl, taside, knuckle, thumb_extra, muneca=None, mid=0):
    extra = knuckles(knuckle, mid)
    extra[T1] = dict(thumb_extra.get(T1, {}))
    if T2 in thumb_extra:
        extra[T2] = dict(thumb_extra[T2])
    if T3 in thumb_extra:
        extra[T3] = dict(thumb_extra[T3])
    data = fingers(curl, tcurl, taside)
    data["muneca"] = muneca or {"y": 50, "z": 45}
    data["extra"] = extra
    return data


THUMB_NOW = {T1: {"y": 30, "z": 4}, T2: {"x": -6}}
THUMB_BOTTOM = {T1: {"y": 18, "z": 16}, T2: {"x": -10}}
THUMB_OPEN = {T1: {"y": 38, "z": 8}, T2: {"x": -4}}
THUMB_RAIL = {T1: {"y": 22, "z": 22}, T2: {"x": -14}, T3: {"x": -8}}
THUMB_PHOTO = {T1: {"y": 28, "z": 14}, T2: {"x": -8}}

CASES = {
    "00_actual": pose(0.46, 0.24, 0.82, 26, THUMB_NOW),
    "01_menos_garra": pose(0.28, 0.24, 0.82, 34, THUMB_NOW),
    "02_arco_suave": pose(0.32, 0.22, 0.70, 32, THUMB_PHOTO),
    "03_pulgar_abajo": pose(0.34, 0.30, 0.58, 30, THUMB_BOTTOM),
    "04_pulgar_extendido": pose(0.30, 0.14, 0.92, 34, THUMB_OPEN),
    "05_foto_c": pose(0.30, 0.20, 0.72, 36, THUMB_PHOTO),
    "06_c_abierta": pose(0.24, 0.16, 0.78, 38, THUMB_OPEN),
    "07_como_o_abierta": pose(0.36, 0.28, 0.55, 20, {T1: {"y": 18, "z": 14}, T2: {"x": -12}}),
    "08_arco_dos_nudillos": pose(0.22, 0.18, 0.74, 36, THUMB_PHOTO, mid=10),
    "09_foto_fuerte": pose(0.34, 0.22, 0.68, 40, THUMB_RAIL),
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
            time.sleep(0.22)

        for name, data in CASES.items():
            page.evaluate("(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data)
            time.sleep(0.22)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
