"""Pone las candidatas de la E al lado de las dos referencias (lamina del
proyecto y foto del usuario), recortadas en cuadrado y a la misma escala, que es
la unica forma de juzgar si la seña se lee.

Uso:
    py tools/compare_e.py            # candidatas de candidates_e.py
"""
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from candidates_e import CANDIDATES
from pose_lab_e import HAND_POS_JS, MEASURE_JS, free_camera

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "tools" / "screenshots" / "referencia"
OUT_DIR = ROOT / "tools" / "screenshots" / "compare_e"
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=cmpE"

# Vista en la direccion de la camara de produccion (theta 0), pero cerca.
# El encuadre debe dejar la mano al ~60% del alto, como en la lamina.
VIEWS = {
    "frente": ("0deg 84deg 0.80m", "26deg"),
    "perfil": ("-80deg 84deg 0.80m", "26deg"),
}


def square(path):
    img = Image.open(path).convert("RGB")
    s = min(img.size)
    left = (img.width - s) // 2
    top = (img.height - s) // 2
    img.crop((left, top, left + s, top + s)).save(path)


def sheet(items, out_path, cols=4, cell=300):
    label_h = 22
    rows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, rows * (cell + label_h)), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)
    for i, (name, path) in enumerate(items):
        x = (i % cols) * cell
        y = (i // cols) * (cell + label_h)
        canvas.paste(
            Image.open(path).convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y)
        )
        draw.rectangle([x, y + cell, x + cell, y + cell + label_h], fill=(20, 30, 50))
        draw.text((x + 6, y + cell + 6), name, fill=(255, 255, 255))
    canvas.save(out_path)
    print("Comparacion:", out_path)


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
        free_camera(page)

        viewer = page.query_selector("#viewer")
        shots = []
        for name, pose in CANDIDATES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", pose
            )
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:16s} d={m['dI']:.2f}/{m['dM']:.2f}/{m['dR']:.2f}/{m['dP']:.2f} "
                f"over={m['overI']:+.2f}/{m['overM']:+.2f}/{m['overP']:+.2f} "
                f"front={m['frontI']:+.2f}/{m['frontM']:+.2f}/{m['frontP']:+.2f} "
                f"gaps={m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            for view, (orbit, fov) in VIEWS.items():
                # El target de model-viewer va amortiguado: hay que dejar pasar
                # frames y volver a saltar, o la mano queda descentrada.
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
                            "o": orbit,
                            "f": fov,
                        },
                    )
                    time.sleep(0.3)
                out = OUT_DIR / f"{name}_{view}.png"
                viewer.screenshot(path=str(out))
                square(out)
                shots.append((f"{name} {view}", out))

        browser.close()

    items = [
        ("REF lamina", REF_DIR / "E.png"),
        ("REF foto", REF_DIR / "E_usuario.png"),
    ] + shots
    sheet([(n, p) for n, p in items if Path(p).exists()], OUT_DIR / "_vs_referencia.png")


if __name__ == "__main__":
    main()
