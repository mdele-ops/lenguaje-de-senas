"""Letra C segun la foto: perfil, arco suave, pulgar opuesto, hueco abierto."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c7"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=c7"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
HAND = "mixamorig1RightHand_035"
T1 = "mixamorig1RightHandThumb1_036"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}


def fingers(curl, thumb_curl=0.36, thumb_aside=0.68):
    return {
        "thumb": {"curl": thumb_curl, "aside": thumb_aside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
    }


def extra(*pairs):
    out = {}
    for name, rot in pairs:
        out[name] = rot
    return out


# Orientacion que dejo la C anterior (poco perfil)
OLD_ARM = extra((ARM, {"z": -18, "y": -25}), (FORE, {"x": 20}), (T1, {"y": 18}))
# Giro mas de perfil para que la C se lea de frente como en la foto
PROFILE_A = extra((ARM, {"z": -22, "y": -38}), (FORE, {"x": 26, "y": -18}))
PROFILE_B = extra((ARM, {"z": -16, "y": -48}), (FORE, {"x": 18, "y": -28}))
PROFILE_C = extra((FORE, {"y": -55, "x": 12}))
PROFILE_D = extra((FORE, {"y": 50, "x": 12}))

CASES = {
    "00_actual": {
        "thumb": {"curl": 0.52, "aside": 0.62},
        "index": {"curl": 0.18, "spread": -4},
        "middle": {"curl": 0.18, "spread": 3},
        "ring": {"curl": 0.18, "spread": 4},
        "pinky": {"curl": 0.18, "spread": 6},
        "extra": extra(
            (I1, {"x": 28}),
            (M1, {"x": 28}),
            (R1, {"x": 28}),
            (P1, {"x": 28}),
            (T1, {"y": 18}),
            (ARM, {"z": -18, "y": -25}),
            (FORE, {"x": 20}),
        ),
    },
    "01_arco40_oldarm": {**fingers(0.40), "extra": OLD_ARM},
    "02_arco42_pa": {**fingers(0.42, 0.34, 0.72), "extra": PROFILE_A},
    "03_arco38_pb": {**fingers(0.38, 0.32, 0.75), "extra": PROFILE_B},
    "04_arco40_fy-55": {**fingers(0.40, 0.34, 0.70), "extra": PROFILE_C},
    "05_arco40_fy50": {**fingers(0.40, 0.34, 0.70), "extra": PROFILE_D},
    "06_arco44_my-50": {
        **fingers(0.44, 0.36, 0.70),
        "muneca": {"y": -50},
        "extra": extra((FORE, {"x": 16})),
    },
    "07_arco42_my50": {
        **fingers(0.42, 0.36, 0.70),
        "muneca": {"y": 50},
        "extra": extra((FORE, {"x": 16})),
    },
    "08_arco40_mz-45": {
        **fingers(0.40, 0.34, 0.70),
        "muneca": {"z": -45},
    },
    "09_arco40_mz45": {
        **fingers(0.40, 0.34, 0.70),
        "muneca": {"z": 45},
    },
    "10_arco36_pa_thumbup": {
        **fingers(0.36, 0.28, 0.80),
        "extra": extra(
            (ARM, {"z": -22, "y": -38}),
            (FORE, {"x": 26, "y": -18}),
            (T1, {"y": 28}),
        ),
    },
    "11_arco40_noorient": {**fingers(0.40, 0.34, 0.70)},
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

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.2)
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_full.png"))
            cam("-0.28m 2.36m 0.20m", "8deg 78deg 0.52m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
