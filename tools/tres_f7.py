"""F: cuanto pueden juntarse los tres dedos sin dejar de leerse a la distancia real.

El primer plano engañaba: con los dedos pegados del todo las costuras existen,
pero en la vista de la portada (camara a 1.55 m, donde la mano mide poco mas de
un centimetro de pantalla) el bloque se lee como una paleta y no se cuentan tres
dedos. Aqui cada variante se mide EN ESA vista: si entre dos dedos se ve el fondo,
que contraste tiene la costura, y cuantas muescas quedan en la silueta de las
puntas, que es lo que de lejos hace que se distingan.
"""
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

import search_e9
from app_f import CAMARA_APP, ENDEREZA_JS
from lab_e2 import hoja
from tres_f import BASE, TRES_JS
from tres_f3 import PIXELES_JS, pose
from tres_f5 import PIEL, analizar, paralelos

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "tres_f7"


def muescas(img, pix):
    """Muescas en el contorno de arriba: de lejos son lo que separa los dedos.

    Se recorre el borde superior de la silueta a lo ancho de los tres dedos y se
    cuentan los valles: con tres dedos de distinto largo bien definidos hay
    escalones; si se han fundido, el contorno es una curva lisa.
    """
    gris = img.convert("L")
    w, h = gris.size
    esc = w / pix["ancho"]
    xs = [p["x"] * esc for d in ("Middle", "Ring", "Pinky") for p in pix[d]]
    ys = [p["y"] * esc for d in ("Middle", "Ring", "Pinky") for p in pix[d]]
    x0, x1 = int(max(0, min(xs) - 6)), int(min(w, max(xs) + 6))
    y0, y1 = int(max(0, min(ys) - 14)), int(min(h, max(ys) + 6))
    fondo = min(gris.getpixel((2, 2)), gris.getpixel((w - 3, 2)))
    borde = []
    for x in range(x0, x1):
        alto = None
        for y in range(y0, y1):
            if gris.getpixel((x, y)) > fondo + PIEL:
                alto = y
                break
        borde.append(alto if alto is not None else y1)
    # valles del contorno: un punto mas bajo (y mayor) que sus vecinos a 3 px
    valles = 0
    for i in range(3, len(borde) - 3):
        if borde[i] - max(borde[i - 3], borde[i + 3]) >= 2:
            if borde[i] >= borde[i - 1] and borde[i] >= borde[i + 1]:
                valles += 1
    return {"valles": valles, "ancho_px": x1 - x0, "caja": (x0, y0, x1, y1)}


CASOS = [
    ("0 abanico de antes", None, 0),
    ("1 nud0.28 c8 pegados", 0.28, 8),
    ("2 nud0.28 c0", 0.28, 0),
    ("3 nud0.22 c4", 0.22, 4),
    ("4 nud0.16 c2", 0.16, 2),
    ("5 nud0.10 c0", 0.10, 0),
    ("6 nud0.28 c-4 abre puntas", 0.28, -4),
    ("7 nud0.22 c-6 abre puntas", 0.22, -6),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fichas = []
    with sync_playwright() as p:
        search_e9.URL = "http://127.0.0.1:8006/practica.html?letra=F&v=f7"
        browser, page = search_e9.abrir(p)
        page.set_viewport_size({"width": 1180, "height": 820})
        time.sleep(1.2)
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
            entera = OUT / f"{clave}_portada.png"
            page.query_selector("#viewer").screenshot(path=str(entera))
            pix = page.evaluate(PIXELES_JS)
            img = Image.open(entera)
            an = analizar(img, pix)
            mu = muescas(img, pix)
            # la mano ocupa poquisimos pixeles: se amplia para poder juzgarla
            x0, y0, x1, y1 = mu["caja"]
            corte = img.crop((x0 - 12, y0 - 10, x1 + 12, y1 + 14))
            corte = corte.resize((corte.width * 5, corte.height * 5), Image.LANCZOS)
            zoom = OUT / f"{clave}_zoom.png"
            corte.save(zoom)
            fichas.append((nombre, zoom))

            def pc(k):
                v = an.get(k)
                return "  - " if v is None else f"{v:4.2f}"

            print(
                f"{nombre:24s} fondo MR {pc('MR_medio')} RP {pc('RP_medio')} | "
                f"costura MR {an['MR_medio_c']:.3f} RP {an['RP_medio_c']:.3f} | "
                f"muescas={mu['valles']} ancho={mu['ancho_px']}px | "
                f"ejes mr={m['mr']['distal']:.3f} rp={m['rp']['distal']:.3f} "
                f"pinza={m['pinza']:.3f}"
            )
        browser.close()

    print("hoja:", hoja(fichas, OUT / "_zoom.png", cols=4, cell=330))


if __name__ == "__main__":
    main()
