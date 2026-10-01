"""K: captura de la pose del catalogo con el medio recto y vertical."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "final_k"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?letra=K&v=k2"


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
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)
        pose = page.evaluate(
            "() => window.LSM_CATALOG.senas.find(s => s.letra === 'K').pose"
        )
        print(pose)
        viewer = page.query_selector("#viewer")
        page.evaluate(
            "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", pose
        )
        time.sleep(0.4)
        viewer.screenshot(path=str(OUT_DIR / "K_app.png"))
        browser.close()


if __name__ == "__main__":
    main()
