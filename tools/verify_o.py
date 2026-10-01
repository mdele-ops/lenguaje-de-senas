"""Comprueba la O por el camino real de la app y contra sus vecinas.

Dos cosas que la hoja de candidatas no puede decir:

1. Que lo que se ve sea lo que hay en el catalogo. Las pruebas usan
   `applyTestPose`; la app usa `mostrarSena`, que ademas busca animaciones por
   nombre y podria estar tapando la pose con un clip generico.
2. Que la O no se confunda con la C ni con la D, que son las otras dos letras
   de la mano en arco. Si no se distinguen a simple vista, la pose no sirve
   aunque las medidas salgan bien.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from hoja_e import encuadrar, preparar
from medida_o import MEDIDA_O_JS, detalle, linea, puntuar
from search_e10 import CAM_PROD_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "referencia"
OUT = ROOT / "tools" / "screenshots" / "verify_o"

LETRAS = ("C", "D", "O", "E")
VISTA = ("0deg 84deg 0.85m", "24deg")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cerca, app = [], []
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        for letra in LETRAS:
            modo = page.evaluate(
                "(l) => window.__LSM_CONTROLLER__.mostrarSena(l).modo", letra
            )
            time.sleep(2.8)
            page.evaluate(CAM_PROD_JS)
            time.sleep(0.4)
            estado = page.inner_text("#anim-info").strip()
            print(f"{letra}: modo={modo} · {estado}")
            if letra == "O":
                o = page.evaluate(MEDIDA_O_JS)
                print(linea("  produccion", o, puntuar(o)))
                print(detalle(o))
            app.append(
                (letra, recorte(page, viewer, OUT / f"{letra}_app.png", False))
            )
            hand = page.evaluate(HAND_TARGET_JS)
            encuadrar(
                page, VISTA[0], VISTA[1],
                "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"]),
            )
            cerca.append(
                (letra, recorte(page, viewer, OUT / f"{letra}_cerca.png", False))
            )
        browser.close()

    ref = [(n, q) for n, q in (
        ("REF foto O", REF / "O_usuario.png"),
        ("REF lamina O", REF / "O.png"),
    ) if q.exists()]
    hoja(ref + cerca, OUT / "_cerca.png", cols=3, cell=320)
    hoja(ref + app, OUT / "_app.png", cols=3, cell=320)


if __name__ == "__main__":
    main()
