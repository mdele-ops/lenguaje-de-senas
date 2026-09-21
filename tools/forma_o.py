"""Retrato y medidas de la O que hay ahora en el catalogo.

Sirve para dos cosas antes de tocar nada: ver desde que angulo se aprecia el
agujero (la O solo se lee si el aro no mira de canto a la camara) y tener el
"antes" contra el que comparar.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from hoja_e import encuadrar, preparar
from compare_e10 import HAND_TARGET_JS, hoja, recorte
from medida_o import MEDIDA_O_JS, detalle, linea, puntuar
from search_e10 import CAM_PROD_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
REF = ROOT / "tools" / "screenshots" / "referencia"
OUT = ROOT / "tools" / "screenshots" / "forma_o"

# Vuelta completa a la mano: se busca desde donde se ve el agujero.
VISTAS = {
    "v-90": ("-90deg 84deg 0.85m", "24deg"),
    "v-60": ("-60deg 84deg 0.85m", "24deg"),
    "v-30": ("-30deg 84deg 0.85m", "24deg"),
    "v000": ("0deg 84deg 0.85m", "24deg"),
    "v+30": ("30deg 84deg 0.85m", "24deg"),
    "v+60": ("60deg 84deg 0.85m", "24deg"),
    "v+90": ("90deg 84deg 0.85m", "24deg"),
    "abajo": ("0deg 115deg 0.85m", "24deg"),
}


def aplicar(page, pose):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.35)


def retratar(page, viewer, nombre, salida, vistas=VISTAS):
    hand = page.evaluate(HAND_TARGET_JS)
    t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
    for vista, (orbit, fov) in vistas.items():
        encuadrar(page, orbit, fov, t)
        salida.setdefault(vista, []).append(
            (nombre, recorte(page, viewer, OUT / f"{nombre}_{vista}.png", False))
        )
    page.evaluate(CAM_PROD_JS)
    time.sleep(0.4)
    salida.setdefault("app", []).append(
        (nombre, recorte(page, viewer, OUT / f"{nombre}_app.png", False))
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads(CATALOGO.read_text("utf-8"))
    actual = next(s for s in cat["senas"] if s["letra"] == "O")["pose"]

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        aplicar(page, actual)
        page.evaluate(CAM_PROD_JS)
        time.sleep(0.4)
        o = page.evaluate(MEDIDA_O_JS)
        print(linea("catalogo", o, puntuar(o)))
        print(detalle(o))

        retratar(page, viewer, "actual", salida)
        browser.close()

    ref = [(n, q) for n, q in (
        ("REF foto", REF / "O_usuario.png"),
        ("REF lamina", REF / "O.png"),
    ) if q.exists()]
    for vista, imgs in salida.items():
        hoja(ref + imgs, OUT / f"_{vista}.png", cols=3, cell=320)


if __name__ == "__main__":
    main()
