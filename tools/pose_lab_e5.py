"""E lab 5: referencia de orientacion. Dibuja letras ya validadas (A, B, D, L)
con las mismas camaras del laboratorio de la E, para leer sin dudas de que lado
queda la palma y el pulgar en cada vista.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e5"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=e5"

LETTERS = ["A", "B", "D", "L", "E"]

VIEWS = {
    "frente": ("0deg 82deg 0.62m", "26deg"),
    "diag": ("-40deg 78deg 0.62m", "26deg"),
    "perfil": ("-80deg 82deg 0.62m", "26deg"),
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 1200})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        for _ in range(120):
            try:
                if page.evaluate(
                    "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
                ):
                    break
            except Exception:
                pass
            time.sleep(0.4)
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")
        for letra in LETTERS:
            page.evaluate(
                "(l) => window.__LSM_CONTROLLER__.getSena(l) && window.__LSM_CONTROLLER__.applyTestPose(window.__LSM_CONTROLLER__.getSena(l).pose)",
                letra,
            )
            time.sleep(0.3)
            free_camera(page)
            hand = page.evaluate(HAND_POS_JS)
            target = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
            for view, (orbit, fov) in VIEWS.items():
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.orbit;
                        mv.fieldOfView = a.fov;
                        mv.jumpCameraToGoal();
                    }""",
                    {"t": target, "orbit": orbit, "fov": fov},
                )
                time.sleep(0.15)
                viewer.screenshot(path=str(OUT_DIR / f"{letra}_{view}.png"))
            print("listo", letra)

        browser.close()


if __name__ == "__main__":
    main()
