"""Letra C LSM: silueta de C como la foto (arco abierto, palma de lado)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c11"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c11"

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}


def pose(
    curl,
    tcurl,
    taside,
    knuckle=12,
    ty=20,
    tz=0,
    t2x=0,
    muneca=None,
    arm=None,
):
    extra = {
        I1: {"x": knuckle},
        M1: {"x": knuckle},
        R1: {"x": knuckle},
        P1: {"x": knuckle},
        T1: {"y": ty, "z": tz},
        T2: {"x": t2x},
    }
    if arm:
        extra[ARM] = arm
    data = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
        "extra": extra,
    }
    if muneca:
        data["muneca"] = muneca
    return data


# 00 = produccion actual. El resto abre una O de perfil (como la foto).
CASES = {
    "00_actual": pose(0.40, 0.32, 0.74, muneca={"y": 50}, arm={"z": -18}),
    "01_arco": pose(0.36, 0.34, 0.68, knuckle=18, ty=18, tz=10, t2x=-12, muneca={"y": 50}, arm={"z": -18}),
    "02_vaso": pose(0.38, 0.36, 0.64, knuckle=16, ty=16, tz=14, t2x=-16, muneca={"y": 52}, arm={"z": -18}),
    "03_foto": pose(0.42, 0.38, 0.70, knuckle=20, ty=22, tz=12, t2x=-14, muneca={"y": 50}, arm={"z": -18}),
    "04_redonda": pose(0.44, 0.40, 0.66, knuckle=18, ty=14, tz=16, t2x=-18, muneca={"y": 48}, arm={"z": -18}),
    "05_abierta": pose(0.34, 0.30, 0.76, knuckle=22, ty=24, tz=8, t2x=-10, muneca={"y": 54}, arm={"z": -18}),
    "06_o_abierta": pose(0.46, 0.40, 0.58, knuckle=12, ty=8, tz=18, t2x=-20, muneca={"y": 50}, arm={"z": -18}),
    "07_knuckle": pose(0.30, 0.36, 0.72, knuckle=26, ty=20, tz=12, t2x=-12, muneca={"y": 50}, arm={"z": -18}),
    "08_thumbup": pose(0.40, 0.28, 0.78, knuckle=16, ty=28, tz=6, t2x=-8, muneca={"y": 50}, arm={"z": -18}),
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
        time.sleep(1.2)

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
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.24)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("0m 2.42m 0.12m", "22deg 84deg 2.4m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
