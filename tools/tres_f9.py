"""F: dedos pegados que se siguen contando, escalonando un poquito la curvatura.

Con los tres dedos pegados y perfectamente paralelos, de lejos se leen como una
paleta: las costuras existen pero el valle de sombra es la mitad de hondo que con
el abanico de antes. En una mano de verdad los dedos juntos no son coplanares: el
anular y el menique se curvan un poco mas, y eso deja escalones en la silueta y
sombra entre ellos. Aqui se prueba ese escalon minimo de curl sin abrir huecos.

Se mide en la vista de la portada (la de lejos, donde se decide si se leen tres
dedos) y tambien de cerca (para confirmar que siguen pegados y que la pinza
pulgar-indice no se mueve).
"""
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from app_f import CAMARA_APP, ENDEREZA_JS
from lab_e2 import MARCO_JS, hoja, orbita
from pinza_f3 import encuadrar
from tres_f import BASE, TRES_JS
from tres_f3 import CENTRO_JS, PIXELES_JS, pose
from tres_f5 import analizar, paralelos
from tres_f8 import abrir, perfil

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "tres_f9"

NUD = 0.28
CIERRE = 8


def con_escalon(z, curls):
    p = pose(NUD, z["Middle"], z["Ring"], z["Pinky"])
    for dedo, curl in zip(("middle", "ring", "pinky"), curls):
        p[dedo] = dict(p[dedo], curl=curl)
    return p


CASOS = [
    ("0 abanico de antes", None),
    ("1 pegados planos", (0.0, 0.0, 0.0)),
    ("2 escalon 0/04/10", (0.0, 0.04, 0.10)),
    ("3 escalon 0/07/16", (0.0, 0.07, 0.16)),
    ("4 escalon 0/10/22", (0.0, 0.10, 0.22)),
    ("5 escalon 2/12/26", (0.02, 0.12, 0.26)),
]


def marcar(img, pix, escala):
    """Copia con los huesos proyectados marcados, para validar el encuadre."""
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    colores = {"Middle": (255, 80, 80), "Ring": (80, 255, 120), "Pinky": (90, 160, 255)}
    for dedo, color in colores.items():
        for p in pix[dedo]:
            x, y = p["x"] * escala, p["y"] * escala
            d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=color, width=2)
    return out


def caja_mano(pix, escala, img, margen=0.45):
    xs = [p["x"] * escala for d in ("Middle", "Ring", "Pinky", "Index") for p in pix[d]]
    ys = [p["y"] * escala for d in ("Middle", "Ring", "Pinky", "Index") for p in pix[d]]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    lado = max(w, h) * (1 + margen)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return (
        int(max(0, cx - lado / 2)),
        int(max(0, cy - lado / 2)),
        int(min(img.width, cx + lado / 2)),
        int(min(img.height, cy + lado / 2)),
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    escala = 3
    lejos, cerca = [], []
    with sync_playwright() as p:
        browser, page = abrir(p, escala=escala)
        page.evaluate(ENDEREZA_JS)
        z = paralelos(page, NUD, CIERRE)
        print("z resueltos:", {k: round(v, 2) for k, v in z.items()})

        for nombre, curls in CASOS:
            clave = nombre.split()[0]
            datos = BASE if curls is None else con_escalon(z, curls)
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", datos)
            time.sleep(0.3)

            # ---- vista de la portada (de lejos) --------------------------------
            page.evaluate(CAMARA_APP)
            time.sleep(0.4)
            m = page.evaluate(TRES_JS)
            visor = OUT / f"{clave}_portada.png"
            page.query_selector("#handViewer").screenshot(path=str(visor))
            pix = page.evaluate(PIXELES_JS)
            img = Image.open(visor)
            pr = perfil(img, pix)
            caja = caja_mano(pix, img.width / pix["ancho"], img)
            marcar(img, pix, img.width / pix["ancho"]).crop(caja).resize(
                (330, 330), Image.LANCZOS
            ).save(OUT / f"{clave}_lejos.png")
            lejos.append((nombre, OUT / f"{clave}_lejos.png"))

            # ---- primer plano frontal (de cerca) ------------------------------
            marco = page.evaluate(MARCO_JS)
            c = page.evaluate(CENTRO_JS)
            encuadrar(page, orbita(marco, (1.0, 0.0, 0.0), radio_palmas=2.4), "20deg",
                      "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"]))
            dedos = OUT / f"{clave}_dedos.png"
            page.query_selector("#handViewer").screenshot(path=str(dedos))
            an = analizar(Image.open(dedos), page.evaluate(PIXELES_JS))
            Image.open(dedos).crop(an["recorte"]).save(OUT / f"{clave}_zoom.png")
            cerca.append((nombre, OUT / f"{clave}_zoom.png"))

            def pc(k):
                v = an.get(k)
                return "  - " if v is None else f"{v:4.2f}"

            hondos = sorted((v for _, v in pr["valles"]), reverse=True)[:3]
            print(
                f"{nombre:20s} LEJOS valles={hondos} | "
                f"CERCA fondo MR {pc('MR_punta')}/{pc('MR_medio')} "
                f"RP {pc('RP_punta')}/{pc('RP_medio')} "
                f"aplastado={an['aplastado'] if an['aplastado'] is None else round(an['aplastado'], 2)} "
                f"| pinza={m['pinza']:.3f}"
            )
        browser.close()

    print("hoja lejos:", hoja(lejos, OUT / "_lejos.png", cols=3, cell=330))
    print("hoja cerca:", hoja(cerca, OUT / "_cerca.png", cols=3, cell=330))


if __name__ == "__main__":
    main()
