"""Comprobacion final de la F: pinza cerrada, tres dedos juntos y contables.

Va por el camino real de la app (`mostrarSena`, lo que corre al pulsar la letra) y
mide sobre esa mano en las dos escalas que importan: de cerca, que no haya hueco
entre dedos ni se pierda la pinza; de lejos (camara de la portada), que el perfil
de brillo siga teniendo dos valles, o sea que se cuenten tres dedos.
"""
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from app_f import CAMARA_APP, ENDEREZA_JS
from junta_f import PINZA_JS
from lab_e2 import MARCO_JS, hoja, orbita
from pinza_f3 import PUNTO_JS, encuadrar
from tres_f import TRES_JS
from tres_f3 import CENTRO_JS, PIXELES_JS
from tres_f5 import analizar
from tres_f8 import abrir, perfil
from tres_f9 import caja_mano

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verifica_f3"

# la F tal como estaba al empezar hoy, para el antes/despues
ORIGINAL = {
    "thumb": {"curl": 0.2},
    "index": {"curl": 0.5, "spread": 8},
    "middle": {"curl": 0.0, "spread": 3},
    "ring": {"curl": 0.0, "spread": 4},
    "pinky": {"curl": 0.0, "spread": 6},
    "extra": {"RightHandThumb1": {"z": 30}},
}


def revisar(page, nombre, salida, escala):
    m = page.evaluate(TRES_JS)
    pinza = page.evaluate(PINZA_JS)

    # ---- de lejos: la vista de la portada -----------------------------------
    page.evaluate(CAMARA_APP)
    time.sleep(0.4)
    visor = OUT / f"{nombre}_portada.png"
    page.query_selector("#handViewer").screenshot(path=str(visor))
    pix = page.evaluate(PIXELES_JS)
    img = Image.open(visor)
    pr = perfil(img, pix)
    caja = caja_mano(pix, img.width / pix["ancho"], img)
    img.crop(caja).resize((420, 420), Image.LANCZOS).save(OUT / f"{nombre}_lejos.png")
    salida.setdefault("lejos", []).append((nombre, OUT / f"{nombre}_lejos.png"))

    # ---- de cerca: frontal sobre los tres dedos ------------------------------
    marco = page.evaluate(MARCO_JS)
    c = page.evaluate(CENTRO_JS)
    encuadrar(page, orbita(marco, (1.0, 0.0, 0.0), radio_palmas=2.4), "20deg",
              "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"]))
    dedos = OUT / f"{nombre}_dedos.png"
    page.query_selector("#handViewer").screenshot(path=str(dedos))
    an = analizar(Image.open(dedos), page.evaluate(PIXELES_JS))
    Image.open(dedos).crop(an["recorte"]).save(OUT / f"{nombre}_zoom.png")
    salida.setdefault("cerca", []).append((nombre, OUT / f"{nombre}_zoom.png"))

    # ---- la pinza ------------------------------------------------------------
    punto = page.evaluate(PUNTO_JS)
    encuadrar(page, orbita(marco, (1.0, 0.0, -0.35), radio_palmas=2.2), "16deg",
              "%.4fm %.4fm %.4fm" % (punto["x"], punto["y"], punto["z"]))
    pin = OUT / f"{nombre}_pinza.png"
    page.query_selector("#handViewer").screenshot(path=str(pin))
    salida.setdefault("pinza", []).append((nombre, pin))

    def pc(k):
        v = an.get(k)
        return "  - " if v is None else f"{v:4.2f}"

    hondos = sorted((v for _, v in pr["valles"]), reverse=True)[:2]
    print(
        f"{nombre:12s} yemas pulgar-indice={pinza['puntas']:.3f} | "
        f"hueco entre dedos (punta/medio/base) MR {pc('MR_punta')}/{pc('MR_medio')}/{pc('MR_base')} "
        f"RP {pc('RP_punta')}/{pc('RP_medio')}/{pc('RP_base')} | "
        f"de lejos, valles del perfil={hondos}"
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    esperada = next(
        s
        for s in json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))["senas"]
        if s["letra"] == "F"
    )["pose"]

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p, escala=3)
        page.evaluate(ENDEREZA_JS)
        print("la pose de la F que ve la pagina coincide con el JSON:",
              page.evaluate("() => window.__LSM_CONTROLLER__.getSena('F').pose") == esperada)

        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", ORIGINAL)
        time.sleep(0.4)
        revisar(page, "1_antes", salida, 3)

        res = page.evaluate(
            "() => window.__LSM_CONTROLLER__.mostrarSena('F', { loop: false })"
        )
        time.sleep(3.4)  # mostrarSena arranca una transicion de 2 s
        print("modo:", res.get("modo"))
        revisar(page, "2_despues", salida, 3)
        browser.close()

    for vista, imgs in salida.items():
        print("hoja:", hoja(imgs, OUT / f"_{vista}.png", cols=2, cell=420))


if __name__ == "__main__":
    main()
