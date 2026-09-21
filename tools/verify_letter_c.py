"""Verifica la letra C desde el boton real de practica.html."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_c_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html?letra=C&v=cfinal22"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        for _ in range(150):
            ready = page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            )
            if ready:
                break
            time.sleep(0.4)
        else:
            raise RuntimeError("El modelo 3D no cargo a tiempo")

        time.sleep(2.0)
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('C')")
        time.sleep(2.4)

        viewer = page.query_selector("#viewer")
        viewer.screenshot(path=str(OUT_DIR / "C_produccion.png"))

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
        viewer.screenshot(path=str(OUT_DIR / "C_cuerpo.png"))

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
        viewer.screenshot(path=str(OUT_DIR / "C_perfil.png"))

        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.30m 2.36m 0.20m';
                mv.cameraOrbit = '-55deg 80deg 0.55m';
                mv.fieldOfView = '20deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "C_palma.png"))

        pose = page.evaluate(
            """() => {
                const s = window.__LSM_CONTROLLER__.getSena('C');
                return s && s.pose;
            }"""
        )
        print("pose C:", pose)
        browser.close()


if __name__ == "__main__":
    main()
