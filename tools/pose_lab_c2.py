"""Segunda pasada letra C: junta fuerte (aduccion opuesta a V) + arco abierto."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?v=c2"

# Junta que funciono en B (opuesta a V: index -42 / middle +42)
JUNTA = {"index": 18, "middle": 6, "ring": -14, "pinky": -24}
JUNTA_SUAVE = {"index": 12, "middle": 4, "ring": -10, "pinky": -18}


def fingers(curl, junta):
    return {
        "index": {"curl": curl, "spread": junta["index"]},
        "middle": {"curl": curl, "spread": junta["middle"]},
        "ring": {"curl": curl, "spread": junta["ring"]},
        "pinky": {"curl": curl, "spread": junta["pinky"]},
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
    "01_junta_arco": {
        "thumb": {"curl": 0.30, "aside": 0.45},
        **fingers(0.36, JUNTA),
        "muneca": {"y": -55},
    },
    "02_junta_media": {
        "thumb": {"curl": 0.32, "aside": 0.42},
        **fingers(0.40, JUNTA),
        "muneca": {"y": -55},
    },
    "03_junta_y70": {
        "thumb": {"curl": 0.32, "aside": 0.45},
        **fingers(0.38, JUNTA),
        "muneca": {"y": -70},
    },
    "04_suave_y55": {
        "thumb": {"curl": 0.30, "aside": 0.42},
        **fingers(0.36, JUNTA_SUAVE),
        "muneca": {"y": -55},
    },
    "05_abierta": {
        "thumb": {"curl": 0.24, "aside": 0.50},
        **fingers(0.30, JUNTA),
        "muneca": {"y": -55},
    },
    "06_cerrada": {
        "thumb": {"curl": 0.38, "aside": 0.40},
        **fingers(0.46, JUNTA),
        "muneca": {"y": -55},
    },
    "07_junta22": {
        "thumb": {"curl": 0.30, "aside": 0.45},
        **fingers(0.36, {"index": 22, "middle": 8, "ring": -16, "pinky": -28}),
        "muneca": {"y": -55},
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
    time.sleep(0.3)


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
            set_cam(page, "-55deg 80deg 0.52m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))
            print("done", name)

        browser.close()


if __name__ == "__main__":
    main()
