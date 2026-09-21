"""Renderiza los candidatos de C con los encuadres de mano que si funcionan."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "review_c"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=creview1"

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

THUMB_OPTS = {
    "arc": {T1: {"y": 34, "z": 6}, T2: {"x": -14}, T3: {"x": -8}},
    "wide": {T1: {"y": 46, "z": 2}, T2: {"x": -10}},
    "straight": {T1: {"y": 34, "z": 8}},
    "up": {T1: {"y": 20, "z": -8}, T2: {"x": -12}},
}


def build(curl, knuckle, mid, tcurl, taside, tname, muneca):
    extra = {
        I1: {"x": knuckle},
        M1: {"x": knuckle},
        R1: {"x": knuckle},
        P1: {"x": knuckle},
        ARM: {"z": -18},
    }
    if mid:
        extra[I2] = {"x": mid}
        extra[M2] = {"x": mid}
        extra[R2] = {"x": mid}
        extra[P2] = {"x": mid}
    for bone, rot in THUMB_OPTS[tname].items():
        extra[bone] = dict(rot)
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": -4},
        "middle": {"curl": curl, "spread": 3},
        "ring": {"curl": curl, "spread": 4},
        "pinky": {"curl": curl, "spread": 6},
        "muneca": dict(muneca),
        "extra": extra,
    }


W90 = {"y": 90}
W90Z = {"y": 90, "z": -30}
W90Z15 = {"y": 90, "z": -15}

CASES = {
    "a_wide_k26_z30": build(0.34, 26, 22, 0.18, 0.6, "wide", W90Z),
    "b_wide_k34_z30": build(0.34, 34, 22, 0.28, 0.35, "wide", W90Z),
    "c_straight_k34": build(0.40, 34, 14, 0.28, 0.6, "straight", W90Z),
    "d_up_k42": build(0.40, 42, 6, 0.28, 0.35, "up", W90Z),
    "e_wide_z15": build(0.34, 34, 22, 0.28, 0.35, "wide", W90Z15),
    "f_wide_z0": build(0.34, 34, 22, 0.28, 0.35, "wide", W90),
    "g_arc_z15": build(0.34, 34, 14, 0.22, 0.5, "arc", W90Z15),
    "h_arc_z0": build(0.34, 34, 14, 0.22, 0.5, "arc", W90),
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
        time.sleep(8)
        ready = False
        for _ in range(80):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                ready = True
                break
            time.sleep(0.3)
        if not ready:
            raise RuntimeError("El modelo 3D no cargo a tiempo")
        time.sleep(1.2)
        viewer = page.query_selector("#viewer")

        def cam(target, orbit, fov):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    if (!mv) return;
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    if (typeof mv.jumpCameraToGoal === 'function') mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.25)

        for name, pose in CASES.items():
            page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose)
            time.sleep(0.3)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT / f"{name}_front.png"))
            cam("-0.30m 2.36m 0.20m", "0deg 82deg 0.52m", "18deg")
            viewer.screenshot(path=str(OUT / f"{name}_mano.png"))
            print("listo", name, flush=True)
        browser.close()


if __name__ == "__main__":
    main()
