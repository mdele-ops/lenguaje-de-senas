"""Candidatos letra C (LSM): mano de perfil, dedos juntos en arco, pulgar opuesto, hueco abierto."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=c1"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

# Junta similar a la B que ya funciono
JUNTA = {
    "index": {"spread": -4},
    "middle": {"spread": 3},
    "ring": {"spread": 4},
    "pinky": {"spread": 6},
}

CASES = {
    "00_actual": {
        "thumb": {"curl": 0.5, "aside": 0.35},
        "index": {"curl": 0.5},
        "middle": {"curl": 0.5},
        "ring": {"curl": 0.5},
        "pinky": {"curl": 0.5},
        "muneca": {"y": -55},
    },
    "01_abierta": {
        "thumb": {"curl": 0.28, "aside": 0.45},
        "index": {"curl": 0.32, **JUNTA["index"]},
        "middle": {"curl": 0.32, **JUNTA["middle"]},
        "ring": {"curl": 0.32, **JUNTA["ring"]},
        "pinky": {"curl": 0.32, **JUNTA["pinky"]},
        "muneca": {"y": -55},
    },
    "02_media": {
        "thumb": {"curl": 0.32, "aside": 0.4},
        "index": {"curl": 0.38, **JUNTA["index"]},
        "middle": {"curl": 0.38, **JUNTA["middle"]},
        "ring": {"curl": 0.38, **JUNTA["ring"]},
        "pinky": {"curl": 0.38, **JUNTA["pinky"]},
        "muneca": {"y": -55},
    },
    "03_media_y70": {
        "thumb": {"curl": 0.32, "aside": 0.4},
        "index": {"curl": 0.38, **JUNTA["index"]},
        "middle": {"curl": 0.38, **JUNTA["middle"]},
        "ring": {"curl": 0.38, **JUNTA["ring"]},
        "pinky": {"curl": 0.38, **JUNTA["pinky"]},
        "muneca": {"y": -70},
    },
    "04_media_y90": {
        "thumb": {"curl": 0.32, "aside": 0.4},
        "index": {"curl": 0.38, **JUNTA["index"]},
        "middle": {"curl": 0.38, **JUNTA["middle"]},
        "ring": {"curl": 0.38, **JUNTA["ring"]},
        "pinky": {"curl": 0.38, **JUNTA["pinky"]},
        "muneca": {"y": -90},
    },
    "05_media_z90": {
        "thumb": {"curl": 0.32, "aside": 0.4},
        "index": {"curl": 0.38, **JUNTA["index"]},
        "middle": {"curl": 0.38, **JUNTA["middle"]},
        "ring": {"curl": 0.38, **JUNTA["ring"]},
        "pinky": {"curl": 0.38, **JUNTA["pinky"]},
        "muneca": {"z": 90},
    },
    "06_thumb_extra": {
        "thumb": {"curl": 0.22, "aside": 0.55},
        "index": {"curl": 0.36, **JUNTA["index"]},
        "middle": {"curl": 0.36, **JUNTA["middle"]},
        "ring": {"curl": 0.36, **JUNTA["ring"]},
        "pinky": {"curl": 0.36, **JUNTA["pinky"]},
        "muneca": {"y": -70},
        "extra": {T1: {"y": 25}},
    },
    "07_arco_fuerte": {
        "thumb": {"curl": 0.35, "aside": 0.5},
        "index": {"curl": 0.42, **JUNTA["index"]},
        "middle": {"curl": 0.42, **JUNTA["middle"]},
        "ring": {"curl": 0.42, **JUNTA["ring"]},
        "pinky": {"curl": 0.42, **JUNTA["pinky"]},
        "muneca": {"y": -70},
    },
    "08_sin_muneca": {
        "thumb": {"curl": 0.32, "aside": 0.45},
        "index": {"curl": 0.36, **JUNTA["index"]},
        "middle": {"curl": 0.36, **JUNTA["middle"]},
        "ring": {"curl": 0.36, **JUNTA["ring"]},
        "pinky": {"curl": 0.36, **JUNTA["pinky"]},
    },
}


def set_cam(page, orbit):
    page.evaluate(
        """(orbit) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = '-0.30m 2.36m 0.20m';
            mv.cameraOrbit = orbit;
            mv.fieldOfView = '18deg';
            mv.jumpCameraToGoal();
        }""",
        orbit,
    )
    time.sleep(0.35)


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
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)

        viewer = page.query_selector("#viewer")

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.25)
            set_cam(page, "8deg 78deg 0.50m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            set_cam(page, "-70deg 80deg 0.52m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
