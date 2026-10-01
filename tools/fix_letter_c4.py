"""Ajuste fino de la C alrededor de la mejor pose medida."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "fix_c4"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=cfix4"

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

CONV = (8, 3, -3, -8)


def build(curl=0.30, knuckle=34, mid=20, tcurl=0.28, taside=0.45,
          thumb=None, wz=-15, spread=CONV):
    extra = {
        I1: {"x": knuckle},
        M1: {"x": knuckle},
        R1: {"x": knuckle},
        P1: {"x": knuckle},
        I2: {"x": mid},
        M2: {"x": mid},
        R2: {"x": mid},
        P2: {"x": mid},
        ARM: {"z": -18},
    }
    for bone, rot in (thumb or {T1: {"y": 34, "z": 8}}).items():
        extra[bone] = dict(rot)
    muneca = {"y": 90}
    if wz:
        muneca["z"] = wz
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": spread[0]},
        "middle": {"curl": curl, "spread": spread[1]},
        "ring": {"curl": curl, "spread": spread[2]},
        "pinky": {"curl": curl, "spread": spread[3]},
        "muneca": muneca,
        "extra": extra,
    }


CASES = {
    "base": build(),
    "v1_pulgar_bajo": build(thumb={T1: {"y": 34, "z": 18}}),
    "v2_pulgar_afuera": build(thumb={T1: {"y": 44, "z": 10}}),
    "v3_dedos_mas": build(curl=0.34, mid=24),
    "v4_dedos_menos": build(curl=0.26, mid=16),
    "v5_wz0": build(wz=0),
    "v6_wz-28": build(wz=-28),
    "v7_pulgar_curvo": build(thumb={T1: {"y": 36, "z": 10}, T2: {"x": -10}}),
    "v8_arco_parejo": build(knuckle=28, mid=26),
    "v9_arco_parejo_bajo": build(knuckle=28, mid=26, thumb={T1: {"y": 36, "z": 16}, T2: {"x": -8}}),
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
        for _ in range(80):
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
            cam("-0.30m 2.36m 0.20m", "0deg 82deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT / f"{name}_mano.png"))
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT / f"{name}_front.png"))
            print("listo", name, flush=True)
        browser.close()


if __name__ == "__main__":
    main()
