"""Prueba de candidatos para la letra B (LSM/ASL): palma al frente,
dedos extendidos y juntos, pulgar doblado sobre la palma."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_b"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?v=b1"

# V separa con index:-42 / middle:+42. Lo contrario junta.
# Valores modestos para no enganchar los dedos.
CASES = {
    "B_actual": {
        "thumb": {"curl": 0.75},
        "index": {"curl": 0.0},
        "middle": {"curl": 0.0},
        "ring": {"curl": 0.0},
        "pinky": {"curl": 0.0},
    },
    "B_junta12": {
        "thumb": {"curl": 0.8, "aside": -0.2},
        "index": {"curl": 0.0, "spread": 12},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": -8},
        "pinky": {"curl": 0.0, "spread": -16},
    },
    "B_junta18": {
        "thumb": {"curl": 0.85, "aside": -0.25},
        "index": {"curl": 0.0, "spread": 18},
        "middle": {"curl": 0.0, "spread": 4},
        "ring": {"curl": 0.0, "spread": -12},
        "pinky": {"curl": 0.0, "spread": -22},
    },
    "B_junta_inv": {
        "thumb": {"curl": 0.8, "aside": -0.2},
        "index": {"curl": 0.0, "spread": -12},
        "middle": {"curl": 0.0, "spread": -3},
        "ring": {"curl": 0.0, "spread": 8},
        "pinky": {"curl": 0.0, "spread": 16},
    },
    "B_pulgar_fuerte": {
        "thumb": {"curl": 0.95, "aside": -0.35},
        "index": {"curl": 0.0, "spread": 12},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": -8},
        "pinky": {"curl": 0.0, "spread": -16},
    },
    "B_pulgar_twist": {
        "thumb": {"curl": 0.82, "aside": -0.15, "twist": 18},
        "index": {"curl": 0.0, "spread": 12},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": -8},
        "pinky": {"curl": 0.0, "spread": -16},
    },
    "B_muneca_y": {
        "thumb": {"curl": 0.82, "aside": -0.2},
        "index": {"curl": 0.0, "spread": 12},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": -8},
        "pinky": {"curl": 0.0, "spread": -16},
        "muneca": {"y": -20},
    },
    "B_muneca_z": {
        "thumb": {"curl": 0.82, "aside": -0.2},
        "index": {"curl": 0.0, "spread": 12},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": -8},
        "pinky": {"curl": 0.0, "spread": -16},
        "muneca": {"z": 12},
    },
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]
        )
        page = browser.new_page(viewport={"width": 900, "height": 900})
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
        else:
            raise RuntimeError("El modelo 3D no cargo a tiempo")

        viewer = page.query_selector("#viewer")

        def set_camera(orbit, target="-0.28m 2.32m 0.18m", fov="22deg"):
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
            time.sleep(0.45)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.35)
            set_camera("8deg 80deg 0.62m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            set_camera("70deg 82deg 0.62m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
