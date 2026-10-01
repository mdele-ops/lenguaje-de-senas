"""F: se leen tres dedos en la vista de la portada? Perfil de brillo del corte.

En esa vista la mano mide unas decenas de pixeles, asi que no vale medir huecos
geometricos: hay que mirar la imagen como la ve la persona. Para cada variante se
toma un corte horizontal a media altura del menique y se saca el perfil de brillo
a lo ancho de los tres dedos. Tres dedos que se leen dan tres lomos con dos valles
entre ellos; un bloque fundido da una sola loma lisa.
"""
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from app_f import CAMARA_APP, ENDEREZA_JS
from lab_e2 import hoja
from tres_f import BASE, TRES_JS
from tres_f3 import PIXELES_JS, pose
from tres_f5 import paralelos

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "tres_f8"
VISOR_CACHE = Path(__file__).resolve().parent / "cache" / "model-viewer.min.js"
URL = "http://127.0.0.1:8006/practica.html?letra=F&v=f8"


def abrir(p, escala=3):
    """Como search_e9.abrir pero con pixeles de sobra para leer el perfil."""
    browser = p.chromium.launch(
        channel="chrome",
        args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
    )
    ctx = browser.new_context(
        viewport={"width": 1180, "height": 820}, device_scale_factor=escala
    )
    page = ctx.new_page()
    if VISOR_CACHE.exists():
        page.route(
            "**/@google/model-viewer*/**",
            lambda ruta: ruta.fulfill(
                path=str(VISOR_CACHE), content_type="application/javascript"
            ),
        )
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_selector("#anim-info", timeout=20000, state="attached")
    for _ in range(150):
        if page.evaluate(
            "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
        ):
            break
        time.sleep(0.4)
    time.sleep(1.0)
    return browser, page


def perfil(img, pix):
    """Perfil de brillo del corte y cuentas de lomos, valles y fondo."""
    gris = img.convert("L")
    w, h = gris.size
    esc = w / pix["ancho"]
    dedos = {
        d: [(p["x"] * esc, p["y"] * esc) for p in pix[d]]
        for d in ("Middle", "Ring", "Pinky")
    }
    fondo = min(gris.getpixel((2, 2)), gris.getpixel((w - 3, 2)))
    # corte a media altura de la falange media del menique (el dedo corto)
    y = int((dedos["Pinky"][1][1] + dedos["Pinky"][2][1]) / 2)
    y = max(1, min(h - 2, y))
    xs = [p[0] for v in dedos.values() for p in v]
    x0, x1 = int(max(0, min(xs) - 12)), int(min(w, max(xs) + 12))
    fila = [gris.getpixel((x, y)) for x in range(x0, x1)]
    # suaviza 3 px: quita el ruido del render sin borrar los valles
    suave = [
        sum(fila[max(0, i - 1):i + 2]) / len(fila[max(0, i - 1):i + 2])
        for i in range(len(fila))
    ]
    piel = [v > fondo + 14 for v in suave]
    bloques = []
    ini = None
    for i, es in enumerate(piel + [False]):
        if es and ini is None:
            ini = i
        elif not es and ini is not None:
            bloques.append((ini, i))
            ini = None
    principal = max(bloques, key=lambda b: b[1] - b[0]) if bloques else (0, 0)
    tramo = suave[principal[0]:principal[1]]
    pico = max(tramo) if tramo else 1
    valles = []
    for i in range(2, len(tramo) - 2):
        if tramo[i] <= min(tramo[i - 2:i]) and tramo[i] <= min(tramo[i + 1:i + 3]):
            hondo = (max(max(tramo[:i]), max(tramo[i:])) - tramo[i]) / pico
            if hondo >= 0.05:
                valles.append((i, round(hondo, 3)))
    return {
        "y": y,
        "bloques": len(bloques),
        "ancho": principal[1] - principal[0],
        "valles": valles,
        "perfil": [round(v / pico, 2) for v in tramo],
        "caja": (x0, int(min(p[1] for v in dedos.values() for p in v)) - 10,
                 x1, int(max(p[1] for v in dedos.values() for p in v)) + 12),
    }


CASOS = [
    ("0 abanico de antes", None, 0),
    ("1 nud0.28 c8", 0.28, 8),
    ("2 nud0.28 c0", 0.28, 0),
    ("3 nud0.22 c0", 0.22, 0),
    ("4 nud0.16 c0", 0.16, 0),
    ("5 nud0.10 c0", 0.10, 0),
    ("6 nud0.22 c-5", 0.22, -5),
    ("7 nud0.16 c-8", 0.16, -8),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fichas = []
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.evaluate(ENDEREZA_JS)
        for nombre, nud, cierre in CASOS:
            clave = nombre.split()[0]
            if nud is None:
                datos = BASE
            else:
                z = paralelos(page, nud, cierre)
                datos = pose(nud, z["Middle"], z["Ring"], z["Pinky"])
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", datos)
            time.sleep(0.3)
            page.evaluate(CAMARA_APP)
            time.sleep(0.4)
            m = page.evaluate(TRES_JS)
            entera = OUT / f"{clave}_visor.png"
            page.query_selector("#handViewer").screenshot(path=str(entera))
            img = Image.open(entera)
            pr = perfil(img, page.evaluate(PIXELES_JS))
            corte = img.crop(pr["caja"])
            corte.resize((corte.width * 3, corte.height * 3), Image.LANCZOS).save(
                OUT / f"{clave}_zoom.png"
            )
            fichas.append((nombre, OUT / f"{clave}_zoom.png"))
            print(
                f"{nombre:20s} bloques={pr['bloques']} ancho={pr['ancho']}px "
                f"valles={pr['valles']} | ejes mr={m['mr']['distal']:.3f} "
                f"rp={m['rp']['distal']:.3f} pinza={m['pinza']:.3f}"
            )
            print(f"    perfil: {pr['perfil']}")
        browser.close()

    print("hoja:", hoja(fichas, OUT / "_zoom.png", cols=4, cell=330))


if __name__ == "__main__":
    main()
