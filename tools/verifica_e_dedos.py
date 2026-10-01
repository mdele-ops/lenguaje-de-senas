"""Comprueba la E corregida por el camino real de la app y junto a sus vecinas.

Llama a `mostrarSena`, que es lo que corre al pulsar la letra, asi se ve que el
catalogo editado llego a la pagina (el controlador prefiere el embebido de
js/catalogo-lsm.js). Saca A, S y T al lado para confirmar que el puno de la E
sigue siendo distinto del de las otras letras de puno.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from e2_medidas import MED_JS, detalle, informe
from lab_e2 import abrir, preparar, publicar, retratar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verifica_e_dedos"
LETRAS = ("E", "A", "S", "T")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    esperada = next(
        x
        for x in json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))["senas"]
        if x["letra"] == "E"
    )["pose"]

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        print("version del catalogo en la pagina:",
              page.evaluate("() => window.__LSM_CONTROLLER__.getCatalog().version"))
        print("la pose de la E que ve la pagina coincide con el JSON:",
              page.evaluate("() => window.__LSM_CONTROLLER__.getSena('E').pose") == esperada)

        for letra in LETRAS:
            res = page.evaluate(
                "(l) => window.__LSM_CONTROLLER__.mostrarSena(l, { loop: false })", letra
            )
            time.sleep(3.4)  # mostrarSena arranca una transicion de 2 s
            m = page.evaluate(MED_JS)
            print(f"{letra}: modo={res.get('modo')} " + informe(letra, m))
            if letra == "E":
                print(detalle(m))
            retratar(page, viewer, letra, OUT, salida)
        browser.close()

    for h in publicar(salida, OUT):
        print("hoja:", h)


if __name__ == "__main__":
    main()
