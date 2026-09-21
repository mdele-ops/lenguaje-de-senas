"""Herramienta rapida para probar poses candidatas via applyTestPose sin editar el JSON.
Uso: define CASES abajo (nombre -> pose dict) y ejecuta. Genera capturas frontal + lateral
en tools/screenshots/lab/<nombre>_front.png y _side.png
"""
import time
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html"

CASES = {
    "A_v1": {
        "thumb": {"curl": 0.35},
        "index": {"curl": 0.5},
        "middle": {"curl": 0.5},
        "ring": {"curl": 0.5},
        "pinky": {"curl": 0.5},
    },
    "E_v1": {
        "thumb": {"curl": 0.45},
        "index": {"curl": 0.65},
        "middle": {"curl": 0.65},
        "ring": {"curl": 0.65},
        "pinky": {"curl": 0.65},
    },
    "N_v1": {
        "thumb": {"curl": 0.8, "twist": 8},
        "index": {"curl": 0.5},
        "middle": {"curl": 0.5},
        "ring": {"curl": 0.5},
        "pinky": {"curl": 0.5},
    },
    "F_v3": {
        "thumb": {"curl": 0.65},
        "index": {"curl": 0.85},
        "middle": {"curl": 0.05},
        "ring": {"curl": 0.05},
        "pinky": {"curl": 0.05},
    },
    "F_v4": {
        "thumb": {"curl": 0.7, "aside": -0.15},
        "index": {"curl": 0.9},
        "middle": {"curl": 0.05},
        "ring": {"curl": 0.05},
        "pinky": {"curl": 0.05},
    },
    "G_v2": {
        "thumb": {"curl": 0.05, "aside": 0.7},
        "index": {"curl": 0.05},
        "middle": {"curl": 0.6},
        "ring": {"curl": 0.6},
        "pinky": {"curl": 0.6},
        "muneca": {"z": 90},
    },
    "Q_v2": {
        "thumb": {"curl": 0.55, "aside": 0.25},
        "index": {"curl": 0.55},
        "middle": {"curl": 0.55},
        "ring": {"curl": 0.55},
        "pinky": {"curl": 0.55},
        "muneca": {"x": 60, "z": 55},
    },
    "H_v1": {
        "thumb": {"curl": 0.55},
        "index": {"curl": 0.05},
        "middle": {"curl": 0.05},
        "ring": {"curl": 0.6},
        "pinky": {"curl": 0.6},
        "muneca": {"z": 90},
    },
    "P_v1": {
        "thumb": {"curl": 0.25, "aside": 0.2},
        "index": {"curl": 0.0},
        "middle": {"curl": 0.5},
        "ring": {"curl": 0.6},
        "pinky": {"curl": 0.6},
        "muneca": {"x": 60},
    },
    "X_v1": {
        "thumb": {"curl": 0.55},
        "index": {"curl": 0.8},
        "middle": {"curl": 0.5},
        "ring": {"curl": 0.5},
        "pinky": {"curl": 0.5},
    },
    "O_v1": {
        "thumb": {"curl": 0.45, "aside": 0.2},
        "index": {"curl": 0.4},
        "middle": {"curl": 0.4},
        "ring": {"curl": 0.4},
        "pinky": {"curl": 0.4},
    },
    "S_v1": {
        "thumb": {"curl": 0.85},
        "index": {"curl": 0.5},
        "middle": {"curl": 0.5},
        "ring": {"curl": 0.5},
        "pinky": {"curl": 0.5},
    },
    "M_v1": {
        "thumb": {"curl": 0.85, "twist": -8},
        "index": {"curl": 0.5},
        "middle": {"curl": 0.5},
        "ring": {"curl": 0.5},
        "pinky": {"curl": 0.5},
    },
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": 1000, "height": 1000})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=15000, state="attached")
        time.sleep(6)

        for _ in range(40):
            ready = page.evaluate("() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()")
            if ready:
                break
            time.sleep(0.3)

        viewer = page.query_selector("#viewer")

        def set_camera(orbit, target="-0.3m 2.3m 0.15m", fov="25deg"):
            page.evaluate(
                """(args) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = args.target;
                    mv.cameraOrbit = args.orbit;
                    mv.fieldOfView = args.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"orbit": orbit, "target": target, "fov": fov},
            )
            time.sleep(0.4)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.3)
            set_camera("5deg 82deg 0.75m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            set_camera("85deg 82deg 0.75m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
