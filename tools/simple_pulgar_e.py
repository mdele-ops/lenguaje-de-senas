"""Pulgares SIN rotaciones por hueso, como los del resto del abecedario.

Todas las demas letras que pliegan el pulgar sobre la palma lo resuelven con
`curl` y como mucho un `aside`/`twist` pequeno: la S -que es este mismo puno-
es solo `{curl: 0.9}`. La E era la excepcion: arrastraba un `extra` de tres
huesos que es justo lo que la doblaba sobre si misma hasta cerrar un anillo.

Aqui se recorre esa familia sencilla sobre los dedos ya calibrados y se saca
una hoja de contactos ampliada para compararla con la foto.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from calibra_e import calibrar, pose
from hoja_e import preparar, retratar
from pulgar_e import PULGAR_JS
from pulgar_e import linea as linea_pulgar
from pulgar_e import puntuar as puntuar_pulgar
from search_e9 import abrir
from search_e10 import CAM_PROD_JS
from simetria_e import SIMETRIA_JS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "simple_pulgar_e"
REF = ROOT / "tools" / "screenshots" / "referencia" / "E_usuario2.png"

DEDOS = {"mcp": 70.0, "pip": 95.0, "dip": 90.0}
CONV = 8

VISTAS = {"frente": ("0deg 84deg 0.95m", "22deg")}

# Segunda vuelta. La primera (curl suelto de 0.80 a 1.00) ya dio la forma
# buena -un pulgar limpio cruzando la palma, sin anillo- y dejo claro que la
# altura la manda `curl` y el cruce hacia el centro lo manda `aside`. Aqui se
# recorre solo esa esquina: puno bien cerrado y el pulgar llevado hacia dentro.
CASOS = [
    ("c90_as+30", {"curl": 0.90, "aside": 0.30}),
    ("c95_as+30", {"curl": 0.95, "aside": 0.30}),
    ("c100_as+30", {"curl": 1.00, "aside": 0.30}),
    ("c90_as+45", {"curl": 0.90, "aside": 0.45}),
    ("c95_as+45", {"curl": 0.95, "aside": 0.45}),
    ("c100_as+45", {"curl": 1.00, "aside": 0.45}),
    ("c95_as+60", {"curl": 0.95, "aside": 0.60}),
    ("c100_as+60", {"curl": 1.00, "aside": 0.60}),
    ("c95_as+45_tw-10", {"curl": 0.95, "aside": 0.45, "twist": -10}),
    ("c95_as+45_tw+10", {"curl": 0.95, "aside": 0.45, "twist": 10}),
    ("c100_as+45_tw-10", {"curl": 1.00, "aside": 0.45, "twist": -10}),
    ("c98_as+38", {"curl": 0.98, "aside": 0.38}),
]

# recorte de la mano en el render (500x500) y en la foto
CAJA = (110, 70, 350, 310)
CELDA = 380


def hoja(nombres):
    ref = Image.open(REF).convert("RGB")
    rw, rh = ref.size
    ims = [(
        "REFERENCIA",
        ref.crop((int(rw * 0.24), int(rh * 0.10), int(rw * 0.82), int(rh * 0.68)))
        .resize((CELDA, CELDA), Image.LANCZOS),
    )]
    for n in nombres:
        im = Image.open(OUT / f"{n}_frente.png").convert("RGB")
        ims.append((n, im.crop(CAJA).resize((CELDA, CELDA), Image.LANCZOS)))

    cols = 5
    filas = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (CELDA * cols, (CELDA + 20) * filas), "white")
    dr = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        f, c = divmod(i, cols)
        sheet.paste(im, (c * CELDA, f * (CELDA + 20)))
        dr.text((c * CELDA + 6, f * (CELDA + 20) + CELDA + 5), n, fill="black")
    sheet.save(OUT / "_hoja.png")
    print("Hoja:", OUT / "_hoja.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        def sim(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            return page.evaluate(SIMETRIA_JS)

        corr, _ = calibrar(sim, 0.0, CONV, objetivo=DEDOS, verbose=False)

        salida, registro = {}, {}
        for nombre, th in CASOS:
            pz = pose(0.0, CONV, corr, dict(th, aside=th.get("aside", 0.0)))
            # `pose` copia los huesos del pulgar de `thumb`; aqui no hay
            # ninguno, que es justamente lo que se quiere probar
            if "twist" in th:
                pz["thumb"]["twist"] = th["twist"]
            sim(pz)
            page.evaluate(CAM_PROD_JS)
            m = page.evaluate(PULGAR_JS)
            print(linea_pulgar(nombre, m, puntuar_pulgar(m)))
            registro[nombre] = {"pose": pz, "m": m}
            retratar(page, viewer, nombre, OUT, salida, vistas=VISTAS, app=False)
        browser.close()

    hoja([n for n, _ in CASOS])
    (OUT / "_casos.json").write_text(json.dumps(registro, indent=2), "utf-8")


if __name__ == "__main__":
    main()
