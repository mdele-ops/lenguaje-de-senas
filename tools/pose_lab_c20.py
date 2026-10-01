"""C20: pulgar horizontal abajo + dedos juntos en arco, como la foto."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c20"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=c20thumb"

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


def build(curl, tcurl, taside, k1, k2, thumb, muneca=None):
    extra = {
        I1: {"x": k1},
        M1: {"x": k1},
        R1: {"x": k1},
        P1: {"x": k1},
        ARM: {"z": -18},
        T1: dict(thumb.get(T1, {})),
    }
    if k2:
        extra[I2] = {"x": k2}
        extra[M2] = {"x": k2}
        extra[R2] = {"x": k2}
        extra[P2] = {"x": k2}
    if T2 in thumb:
        extra[T2] = dict(thumb[T2])
    if T3 in thumb:
        extra[T3] = dict(thumb[T3])
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": -4},
        "middle": {"curl": curl, "spread": 3},
        "ring": {"curl": curl, "spread": 4},
        "pinky": {"curl": curl, "spread": 6},
        "muneca": muneca or {"y": 50, "z": 45},
        "extra": extra,
    }


# Pulgar como riel inferior de la C (opuesto a los dedos, poco "arriba")
RAIL = {T1: {"y": 12, "z": 24}, T2: {"x": -12}}
RAIL2 = {T1: {"y": 8, "z": 30}, T2: {"x": -16}, T3: {"x": -6}}
HORIZ = {T1: {"y": 20, "z": 20}, T2: {"x": -10}}
OPEN = {T1: {"y": 38, "z": 8}, T2: {"x": -4}}

CASES = {
    "a_04base": build(0.30, 0.14, 0.92, 34, 0, OPEN),
    "b_05base": build(0.30, 0.20, 0.72, 36, 0, {T1: {"y": 28, "z": 14}, T2: {"x": -8}}),
    "c_rail": build(0.30, 0.22, 0.50, 34, 6, RAIL),
    "d_rail2": build(0.28, 0.26, 0.42, 36, 8, RAIL2),
    "e_horiz": build(0.32, 0.18, 0.58, 38, 4, HORIZ),
    "f_foto": build(0.28, 0.16, 0.62, 40, 8, HORIZ),
    "g_junto": build(0.26, 0.18, 0.55, 38, 10, RAIL),
    "h_perfil": build(0.30, 0.18, 0.58, 36, 6, HORIZ, {"y": 55, "z": 52}),
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

        for name, data in CASES.items():
            page.evaluate("(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data)
            time.sleep(0.2)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.48m", "16deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)
        browser.close()


if __name__ == "__main__":
    main()
