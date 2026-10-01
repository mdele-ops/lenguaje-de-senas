"""Comprueba la F por el camino real de la app y la compara con la de antes.

Llama a `mostrarSena`, que es lo que corre al pulsar la letra, para confirmar que
la pose editada llego a la pagina (el controlador prefiere el catalogo embebido
de js/catalogo-lsm.js). Saca la vista de produccion y dos primeros planos de la
pinza, y repite lo mismo con la pose anterior para tener el antes/despues.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from junta_f import PINZA_JS, informe
from lab_e2 import MARCO_JS, abrir, hoja, orbita, preparar, recorte
from pinza_f3 import PUNTO_JS, encuadrar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verifica_f"

ANTES = {
    "thumb": {"curl": 0.2},
    "index": {"curl": 0.5, "spread": 8},
    "middle": {"curl": 0.0, "spread": 3},
    "ring": {"curl": 0.0, "spread": 4},
    "pinky": {"curl": 0.0, "spread": 6},
    "extra": {"RightHandThumb1": {"z": 30}},
}

VISTAS = {
    "mano": ((1.0, 0.0, -0.2), 4.6, "24deg", False),
    "pinza": ((1.0, 0.0, -0.35), 2.4, "16deg", True),
    "arriba": ((0.5, 0.75, -0.3), 2.4, "16deg", True),
}


def retratar(page, viewer, nombre, salida):
    marco = page.evaluate(MARCO_JS)
    punto = page.evaluate(PUNTO_JS)
    centro = marco["centro"]
    for vista, (pesos, radio, fov, cerca) in VISTAS.items():
        c = punto if cerca else centro
        encuadrar(
            page,
            orbita(marco, pesos, radio_palmas=radio),
            fov,
            "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"]),
        )
        salida.setdefault(vista, []).append(
            (nombre, recorte(page, viewer, OUT / f"{nombre}_{vista}.png"))
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
        browser, page = abrir(p)
        viewer = preparar(page)

        print("la pose de la F que ve la pagina coincide con el JSON:",
              page.evaluate("() => window.__LSM_CONTROLLER__.getSena('F').pose") == esperada)

        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", ANTES)
        time.sleep(0.4)
        print(informe("antes", page.evaluate(PINZA_JS)))
        retratar(page, viewer, "1_antes", salida)

        res = page.evaluate(
            "() => window.__LSM_CONTROLLER__.mostrarSena('F', { loop: false })"
        )
        time.sleep(3.4)  # mostrarSena arranca una transicion de 2 s
        m = page.evaluate(PINZA_JS)
        print(f"despues (modo={res.get('modo')}) " + informe("", m))
        retratar(page, viewer, "2_despues", salida)
        browser.close()

    for vista, imgs in salida.items():
        print("hoja:", hoja(imgs, OUT / f"_{vista}.png", cols=2, cell=420))


if __name__ == "__main__":
    main()
