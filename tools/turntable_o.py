"""Giro de camara alrededor de la mano para entender la forma real de la O.

Uso:
    py tools/turntable_o.py            -> pose de la letra O del catalogo
    py tools/turntable_o.py NOMBRE     -> subcarpeta de salida
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
NAME = sys.argv[1] if len(sys.argv) > 1 else "turntable_o"
OUT_DIR = ROOT / "tools" / "screenshots" / NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=tt"

# Centro aproximado de la mano derecha del personaje.
HAND_TARGET = "-0.30m 2.37m 0.18m"


def _poll_ready(page, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            if page.evaluate(
                "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
            ):
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def open_ready_page(browser, attempts=4):
    last = None
    for attempt in range(1, attempts + 1):
        page = browser.new_page(viewport={"width": 900, "height": 900})
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("#anim-info", timeout=20000, state="attached")
            if _poll_ready(page, 45):
                time.sleep(1.0)
                return page
            last = "modelo no listo"
        except Exception as err:
            last = repr(err)[:200]
        print(f"intento {attempt}/{attempts} fallido ({last}); recargando...")
        page.close()
    raise RuntimeError(f"El modelo 3D no cargo a tiempo: {last}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = open_ready_page(browser)

        # Pose real de la letra O del catalogo
        page.evaluate(
            """() => {
                const c = window.__LSM_CONTROLLER__;
                c.applyTestPose(c.getSena('O').pose);
            }"""
        )
        time.sleep(0.4)

        viewer = page.query_selector("#viewer")
        for theta in range(-120, 121, 20):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.theta + 'deg 82deg 0.42m';
                    mv.fieldOfView = '26deg';
                    mv.jumpCameraToGoal();
                }""",
                {"target": HAND_TARGET, "theta": theta},
            )
            time.sleep(0.25)
            viewer.screenshot(path=str(OUT_DIR / f"theta_{theta:+04d}.png"))
            print("theta", theta)

        browser.close()
        print("->", OUT_DIR)


if __name__ == "__main__":
    main()
