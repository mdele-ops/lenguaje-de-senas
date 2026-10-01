"""Comprueba la F con los tres dedos juntos, por el camino real de la app.

Llama a `mostrarSena`, que es lo que corre al pulsar la letra, para asegurar que
la pose del catalogo llego a la pagina, y sobre ESA mano mide: costuras entre
dedos por zonas (analisis de imagen), aplastamiento del bloque de tres dedos y la
pinza pulgar-indice. Repite lo mismo con la pose anterior para el antes/despues.
"""
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from junta_f import PINZA_JS
from lab_e2 import MARCO_JS, abrir, hoja, orbita, preparar, recorte
from pinza_f3 import PUNTO_JS, encuadrar
from tres_f import TRES_JS
from tres_f3 import CENTRO_JS, PIXELES_JS
from tres_f5 import analizar, fila_informe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verifica_f2"

ANTES = {
    "thumb": {"curl": 0.45, "aside": -0.1},
    "index": {"curl": 0.52, "spread": 14},
    "middle": {"curl": 0.0, "spread": 3},
    "ring": {"curl": 0.0, "spread": 4},
    "pinky": {"curl": 0.0, "spread": 6},
    "extra": {"RightHandThumb1": {"z": 50}},
}

Z0 = {"Middle": 0.0, "Ring": 0.0, "Pinky": 0.0}


def revisar(page, nombre, salida):
    """Analiza la mano que hay puesta y guarda las vistas."""
    m = page.evaluate(TRES_JS)
    pinza = page.evaluate(PINZA_JS)
    marco = page.evaluate(MARCO_JS)

    # vista frontal cerrada sobre los tres dedos: la que se analiza
    c = page.evaluate(CENTRO_JS)
    encuadrar(page, orbita(marco, (1.0, 0.0, 0.0), radio_palmas=2.4), "20deg",
              "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"]))
    entera = OUT / f"{nombre}_dedos.png"
    page.query_selector("#handViewer").screenshot(path=str(entera))
    an = analizar(Image.open(entera), page.evaluate(PIXELES_JS))
    img = Image.open(entera)
    img.crop(an["recorte"]).save(OUT / f"{nombre}_zoom.png")
    salida.setdefault("dedos", []).append((nombre, OUT / f"{nombre}_zoom.png"))

    # la mano entera y la pinza, para no perder de vista la letra
    viewer = page.query_selector("#viewer")
    centro = marco["centro"]
    encuadrar(page, orbita(marco, (1.0, 0.0, -0.2), radio_palmas=4.6), "24deg",
              "%.4fm %.4fm %.4fm" % (centro["x"], centro["y"], centro["z"]))
    salida.setdefault("mano", []).append(
        (nombre, recorte(page, viewer, OUT / f"{nombre}_mano.png"))
    )
    punto = page.evaluate(PUNTO_JS)
    encuadrar(page, orbita(marco, (1.0, 0.0, -0.35), radio_palmas=2.4), "16deg",
              "%.4fm %.4fm %.4fm" % (punto["x"], punto["y"], punto["z"]))
    salida.setdefault("pinza", []).append(
        (nombre, recorte(page, viewer, OUT / f"{nombre}_pinza.png"))
    )
    print(fila_informe(nombre, Z0, m, an))
    print(f"    {'':18s} yemas pulgar-indice={pinza['puntas']:.3f} "
          f"(contacto en t={pinza['dondeT']:.2f} i={pinza['dondeI']:.2f})")
    return m, pinza, an


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    esperada = next(
        s
        for s in json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))["senas"]
        if s["letra"] == "F"
    )["pose"]

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.5)
        preparar(page)

        print("la pose de la F que ve la pagina coincide con el JSON:",
              page.evaluate("() => window.__LSM_CONTROLLER__.getSena('F').pose") == esperada)

        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", ANTES)
        time.sleep(0.4)
        revisar(page, "1_antes", salida)

        res = page.evaluate(
            "() => window.__LSM_CONTROLLER__.mostrarSena('F', { loop: false })"
        )
        time.sleep(3.4)  # mostrarSena arranca una transicion de 2 s
        print("modo:", res.get("modo"))
        revisar(page, "2_despues", salida)
        browser.close()

    for vista, imgs in salida.items():
        print("hoja:", hoja(imgs, OUT / f"_{vista}.png", cols=2, cell=420))


if __name__ == "__main__":
    main()
