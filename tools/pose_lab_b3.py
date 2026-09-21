"""Letra B: pulgar hacia ARRIBA (no doblado hacia abajo sobre la palma)."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_b3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?v=b3"

FINGERS = {
    "index": {"curl": 0.0, "spread": 14},
    "middle": {"curl": 0.0, "spread": 4},
    "ring": {"curl": 0.0, "spread": -10},
    "pinky": {"curl": 0.0, "spread": -20},
}

CASES = {
    "down_actual": {"thumb": {"curl": 0.74, "aside": -0.5}, **FINGERS},
    "curl0": {"thumb": {"curl": 0.0}, **FINGERS},
    "up_m03": {"thumb": {"curl": -0.3}, **FINGERS},
    "up_m05": {"thumb": {"curl": -0.5}, **FINGERS},
    "up_m07": {"thumb": {"curl": -0.7}, **FINGERS},
    "up_m05_as": {"thumb": {"curl": -0.5, "aside": -0.4}, **FINGERS},
    "up_m05_ap": {"thumb": {"curl": -0.5, "aside": 0.4}, **FINGERS},
    "up_m04_tw": {"thumb": {"curl": -0.4, "twist": 20}, **FINGERS},
    "low_02_as": {"thumb": {"curl": 0.2, "aside": -0.5}, **FINGERS},
    "low_02_ap": {"thumb": {"curl": 0.2, "aside": 0.5}, **FINGERS},
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

        def cam(orbit):
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
            time.sleep(0.4)

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.3)
            cam("10deg 78deg 0.48m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
