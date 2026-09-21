"""Segunda pasada letra B: afinar junta de dedos y plegado del pulgar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_b2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?v=b2"

BASE_FINGERS = {
    "index": {"curl": 0.0, "spread": 14},
    "middle": {"curl": 0.0, "spread": 4},
    "ring": {"curl": 0.0, "spread": -10},
    "pinky": {"curl": 0.0, "spread": -20},
}

CASES = {
    "B_junta14": {
        "thumb": {"curl": 0.75, "aside": -0.2},
        **BASE_FINGERS,
    },
    "B_aside_m1": {
        "thumb": {"curl": 0.7, "aside": -1.0},
        **BASE_FINGERS,
    },
    "B_aside_p1": {
        "thumb": {"curl": 0.7, "aside": 1.0},
        **BASE_FINGERS,
    },
    "B_aside_m18": {
        "thumb": {"curl": 0.7, "aside": -1.8},
        **BASE_FINGERS,
    },
    "B_aside_p18": {
        "thumb": {"curl": 0.7, "aside": 1.8},
        **BASE_FINGERS,
    },
    "B_twist_p40": {
        "thumb": {"curl": 0.75, "aside": -0.2, "twist": 40},
        **BASE_FINGERS,
    },
    "B_twist_m40": {
        "thumb": {"curl": 0.75, "aside": -0.2, "twist": -40},
        **BASE_FINGERS,
    },
    "B_spread_thumb": {
        "thumb": {"curl": 0.7, "aside": -0.4, "spread": 25},
        **BASE_FINGERS,
    },
    "B_spread_thumb_neg": {
        "thumb": {"curl": 0.7, "aside": -0.4, "spread": -25},
        **BASE_FINGERS,
    },
    "B_compact": {
        "thumb": {"curl": 0.72, "aside": -0.55},
        "index": {"curl": 0.0, "spread": 16},
        "middle": {"curl": 0.0, "spread": 5},
        "ring": {"curl": 0.0, "spread": -12},
        "pinky": {"curl": 0.0, "spread": -24},
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

        def set_camera(orbit, target="-0.32m 2.38m 0.22m", fov="18deg"):
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
            set_camera("12deg 78deg 0.48m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            set_camera("-55deg 80deg 0.50m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_thumb.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
