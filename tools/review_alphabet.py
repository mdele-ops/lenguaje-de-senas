"""Genera capturas de acercamiento (mismo angulo de camara que produccion, solo
mas zoom) para las 27 letras + Neutral, para revisar visualmente cada
configuracion dactilologica contra su descripcion."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "review"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8123/practica.html"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": 1000, "height": 1000})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=15000, state="attached")
        time.sleep(8)

        viewer = page.query_selector("#viewer")
        buttons = page.query_selector_all(".letter-pill")
        labels = [b.text_content().strip() for b in buttons]
        print("Botones:", labels)

        for i, btn in enumerate(buttons):
            label = labels[i]
            page.evaluate("(el) => el.click()", btn)
            time.sleep(2.6)
            page.evaluate(
                """
                () => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.3m 2.3m 0.15m';
                    mv.cameraOrbit = '5deg 82deg 0.75m';
                    mv.fieldOfView = '25deg';
                    mv.jumpCameraToGoal();
                }
                """
            )
            time.sleep(0.6)
            safe_label = label.replace("Ñ", "N").replace("○", "NEUTRAL")
            out_path = OUT_DIR / f"{i:02d}_{safe_label}.png"
            viewer.screenshot(path=str(out_path))
            print("Guardada:", out_path.name)

        browser.close()


if __name__ == "__main__":
    main()
