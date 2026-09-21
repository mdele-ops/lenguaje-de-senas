"""Letra B actual + extras en pulgar para que el tip suba."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_b5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?v=b5"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"

B = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.0, "spread": 14},
    "middle": {"curl": 0.0, "spread": 4},
    "ring": {"curl": 0.0, "spread": -10},
    "pinky": {"curl": 0.0, "spread": -20},
}


def case(name, thumb=None, extra=None):
    pose = dict(B)
    if thumb is not None:
        pose["thumb"] = thumb
    if extra:
        pose["extra"] = extra
    return name, pose


CASES = dict(
    [
        case("actual"),
        case("t2z-50", extra={T2: {"z": -50}}),
        case("t2z50", extra={T2: {"z": 50}}),
        case("t2z-80", extra={T2: {"z": -80}}),
        case("t2y-50", extra={T2: {"y": -50}}),
        case("t2y50", extra={T2: {"y": 50}}),
        case("t2x-50", extra={T2: {"x": -50}}),
        case("t2x50", extra={T2: {"x": 50}}),
        case("t1z40", extra={T1: {"z": 40}}),
        case("t1z-40", extra={T1: {"z": -40}}),
        case("t1z60", extra={T1: {"z": 60}}),
        case("t1y40", extra={T1: {"y": 40}}),
        case("t1y-40", extra={T1: {"y": -40}}),
        case("t3z-50", extra={T3: {"z": -50}}),
        case("t3x-50", extra={T3: {"x": -50}}),
        case("low_t1z50", thumb={"curl": 0.25, "aside": -0.35}, extra={T1: {"z": 50}}),
        case("low_t1z-50", thumb={"curl": 0.25, "aside": -0.35}, extra={T1: {"z": -50}}),
        case("mid_t1z45_t2x-30", thumb={"curl": 0.4, "aside": -0.4}, extra={T1: {"z": 45}, T2: {"x": -30}}),
        case("a_like", thumb={"curl": 0.35}),
        case("a_like_as", thumb={"curl": 0.35, "aside": -0.4}),
        case("a_like_t1z40", thumb={"curl": 0.32, "aside": -0.3}, extra={T1: {"z": 40}}),
        case("upfold", thumb={"curl": 0.45, "aside": -0.2}, extra={T1: {"z": 70}, T2: {"z": -40}}),
        case("upfold2", thumb={"curl": 0.4}, extra={T1: {"z": -70}, T2: {"z": 40}}),
    ]
)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]
        )
        page = browser.new_page(viewport={"width": 800, "height": 800})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        time.sleep(6)
        for _ in range(50):
            ready = page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            )
            if ready:
                break
            time.sleep(0.3)

        viewer = page.query_selector("#viewer")
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '10deg 78deg 0.48m';
                mv.fieldOfView = '18deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.35)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.28)
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
