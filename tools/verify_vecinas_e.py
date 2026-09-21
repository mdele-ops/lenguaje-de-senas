"""Comprueba que la E no se confunde con sus vecinas de puño (A y S).

Las tres se dibujan por el camino de produccion y se ponen en una hoja: si la E
no se distingue a simple vista de la A o la S, la pose no sirve.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from verify_letter_e import REF_DIR, sheet, square

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "verify_vecinas_e"
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vecE"

LETRAS = ["A", "E", "S"]
ORBIT = "0deg 84deg 0.80m"
FOV = "26deg"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
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
        shots = []
        for letra in LETRAS:
            page.evaluate("(l) => window.__LSM_CONTROLLER__.mostrarSena(l)", letra)
            time.sleep(2.8)
            free_camera(page)
            hand = page.evaluate(HAND_POS_JS)
            for _ in range(2):
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.o;
                        mv.fieldOfView = a.f;
                        mv.jumpCameraToGoal();
                    }""",
                    {
                        "t": "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"]),
                        "o": ORBIT,
                        "f": FOV,
                    },
                )
                time.sleep(0.3)
            out = OUT_DIR / f"{letra}.png"
            viewer.screenshot(path=str(out))
            square(out)
            shots.append((f"letra {letra}", out))
            print("listo", letra)

        browser.close()

    sheet(
        [("REF E lamina", REF_DIR / "E.png")] + shots,
        OUT_DIR / "_A_E_S.png",
        cols=4,
    )


if __name__ == "__main__":
    main()
