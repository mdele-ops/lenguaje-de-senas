"""Verifica la letra D desde el boton real de practica.html."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_d_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?letra=D&v=dfinal2"


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

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('D')")
        time.sleep(2.4)

        viewer = page.query_selector("#viewer")
        viewer.screenshot(path=str(OUT_DIR / "D_produccion.png"))

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
        viewer.screenshot(path=str(OUT_DIR / "D_cuerpo.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '8deg 78deg 0.50m';
                mv.fieldOfView = '18deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "D_mano.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '-40deg 80deg 0.55m';
                mv.fieldOfView = '20deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "D_palma.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '12deg 76deg 0.42m';
                mv.fieldOfView = '16deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "D_yemas.png"))

        info = page.evaluate(
            """() => {
                const s = window.__LSM_CONTROLLER__.getSena('D');
                return {
                  pose: s && s.pose,
                  desc: s && s.descripcion,
                  status: document.getElementById('anim-info') && document.getElementById('anim-info').textContent
                };
            }"""
        )
        print("pose D:", info)
        browser.close()


if __name__ == "__main__":
    main()
