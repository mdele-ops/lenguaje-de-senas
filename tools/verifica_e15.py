"""Comprueba la E por el camino real de la app y que las vecinas siguen bien.

No usa `applyTestPose`: llama a `mostrarSena`, que es lo que corre al pulsar la
letra, para que se vea que el cambio del catalogo llega a la pagina (el
controlador prefiere el catalogo embebido de js/catalogo-lsm.js, asi que si ese
no se hubiese sincronizado, aqui saldria la pose vieja).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from hoja_e import preparar, publicar, retratar
from pulgar_e import PULGAR_JS
from pulgar_e import linea as linea_pulgar
from pulgar_e import puntuar as puntuar_pulgar
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, detalle, informe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verifica_e15"
LETRAS = ("E", "A", "S", "T", "O", "C")

VISTAS = {"frente": ("0deg 84deg 0.95m", "22deg")}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    esperada = next(
        x for x in json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))["senas"]
        if x["letra"] == "E"
    )["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        version = page.evaluate(
            "() => window.__LSM_CONTROLLER__.getCatalog().version"
        )
        en_pagina = page.evaluate(
            "() => window.__LSM_CONTROLLER__.getSena('E').pose"
        )
        print("version del catalogo en la pagina:", version)
        print(
            "la pose de la E que ve la pagina coincide con el JSON:",
            en_pagina == esperada,
        )

        salida = {}
        for letra in LETRAS:
            res = page.evaluate(
                "(l) => window.__LSM_CONTROLLER__.mostrarSena(l, { loop: false })",
                letra,
            )
            # mostrarSena arranca una transicion de 2 s; hay que esperarla
            time.sleep(3.2)
            s = page.evaluate(SIMETRIA_JS)
            print(f"{letra}: modo={res.get('modo')} {informe(letra, s)}")
            if letra == "E":
                print(detalle(s))
                m = page.evaluate(PULGAR_JS)
                print("  ", linea_pulgar("pulgar", m, puntuar_pulgar(m)))
            retratar(page, viewer, letra, OUT, salida, vistas=VISTAS)
        browser.close()

    publicar(salida, OUT, cols=4, cell=300)


if __name__ == "__main__":
    main()
