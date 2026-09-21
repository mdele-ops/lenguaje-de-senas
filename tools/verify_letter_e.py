"""Verifica la letra E por el camino de produccion: catalogo embebido +
mostrarSena, como si el usuario pulsara el boton en practica.html.

Deja las capturas junto a las referencias en screenshots/lab_e_final.
"""
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, MEASURE_JS, free_camera

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "tools" / "screenshots" / "referencia"
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e_final"
URL = "http://127.0.0.1:8123/practica.html?letra=E&v=efinal2"

# La primera es la camara real de la app; las demas son para revisar la pose.
VISTAS = {
    "app": (None, "0deg 84deg 2.5m", "30deg"),
    "frente": ("mano", "0deg 84deg 0.80m", "26deg"),
    "perfil": ("mano", "-80deg 84deg 0.80m", "26deg"),
    "arriba": ("mano", "0deg 40deg 0.80m", "26deg"),
}


def square(path):
    img = Image.open(path).convert("RGB")
    s = min(img.size)
    left = (img.width - s) // 2
    top = (img.height - s) // 2
    img.crop((left, top, left + s, top + s)).save(path)


def sheet(items, out_path, cols=3, cell=320):
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
    print("Hoja:", out_path)


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

        pose = page.evaluate("() => window.__LSM_CONTROLLER__.getSena('E').pose")
        print("pose E del catalogo embebido:")
        for clave in ("thumb", "index", "middle", "ring", "pinky", "muneca"):
            if clave in pose:
                print(f"  {clave}: {pose[clave]}")

        # Camino de produccion, con la transicion de 2 s.
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('E')")
        time.sleep(3.0)
        print("estado:", page.inner_text("#anim-info").strip()[:120])

        m = page.evaluate(MEASURE_JS)
        print(
            "yema -> pulgar      : "
            f"I={m['dI']:.2f} M={m['dM']:.2f} R={m['dR']:.2f} P={m['dP']:.2f} (palmas)"
        )
        print(
            "yema encima/delante : "
            f"over={m['overI']:+.2f}/{m['overM']:+.2f}/{m['overP']:+.2f} "
            f"front={m['frontI']:+.2f}/{m['frontM']:+.2f}/{m['frontP']:+.2f}"
        )
        print(
            "dedos juntos        : "
            f"{m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f}   pulgar tumbado={m['tHoriz']:.2f}"
        )

        viewer = page.query_selector("#viewer")
        shots = []
        free_camera(page)
        hand = page.evaluate(HAND_POS_JS)
        for name, (centro, orbit, fov) in VISTAS.items():
            target = (
                "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
                if centro
                else "0m 2.45m 0.15m"
            )
            for _ in range(2):
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.o;
                        mv.fieldOfView = a.f;
                        mv.jumpCameraToGoal();
                    }""",
                    {"t": target, "o": orbit, "f": fov},
                )
                time.sleep(0.3)
            out = OUT_DIR / f"E_{name}.png"
            viewer.screenshot(path=str(out))
            if centro:
                square(out)
            shots.append((f"E {name}", out))

        browser.close()

    items = [
        ("REF lamina", REF_DIR / "E.png"),
        ("REF foto", REF_DIR / "E_usuario.png"),
    ] + shots
    sheet([(n, p) for n, p in items if Path(p).exists()], OUT_DIR / "_vs_referencia.png")


if __name__ == "__main__":
    main()
