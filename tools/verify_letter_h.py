"""Verifica la letra H desde el boton real de practica.html."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_h_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?letra=H&v=hfinal1"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        time.sleep(7)

        for _ in range(50):
            ready = page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            )
            if ready:
                break
            time.sleep(0.3)
        else:
            raise RuntimeError("El modelo 3D no cargo a tiempo")

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('H')")
        time.sleep(2.4)

        viewer = page.query_selector("#viewer")
        viewer.screenshot(path=str(OUT_DIR / "H_produccion.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '0m 2.40m 0.15m';
                mv.cameraOrbit = '28deg 84deg 2.4m';
                mv.fieldOfView = '30deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "H_cuerpo.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.08m 2.36m 0.20m';
                mv.cameraOrbit = '20deg 78deg 0.55m';
                mv.fieldOfView = '18deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "H_mano.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.08m 2.36m 0.20m';
                mv.cameraOrbit = '-15deg 82deg 0.58m';
                mv.fieldOfView = '18deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "H_frente.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.08m 2.36m 0.20m';
                mv.cameraOrbit = '55deg 78deg 0.60m';
                mv.fieldOfView = '18deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "H_oblicua.png"))

        print("OK:", OUT_DIR)
        browser.close()


if __name__ == "__main__":
    main()
