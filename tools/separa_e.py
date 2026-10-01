"""Hoja de contactos de la E variando lo que amontona los dedos.

El `nudillos` alto junta las cuatro raices casi en un punto: los dedos se
meten unos dentro de otros y el puno se lee como un bulto. Aqui se comparan
varios valores de `nudillos` y de `spread` para elegir mirando.
"""
import copy
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from e2_medidas import MED_JS, detalle, informe
from lab_e2 import abrir, aplicar, preparar, publicar, retratar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "separa_e"

FINGERS = ("index", "middle", "ring", "pinky")


def variante(base, nudillos=None, spreads=None, curls=None, largo=None):
    p = copy.deepcopy(base)
    if nudillos is not None:
        p["nudillos"] = nudillos
    if spreads is not None:
        for finger, s in zip(FINGERS, spreads):
            p[finger]["spread"] = s
    if curls is not None:
        for finger, c in zip(FINGERS, curls):
            p[finger]["curl"] = c
    if largo is not None:
        p["largo"] = dict(largo)
    return p


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    base = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    casos = [
        ("A nud 0.54 (actual)", variante(base)),
        ("B nud 0.35", variante(base, nudillos=0.35)),
        ("C nud 0.20", variante(base, nudillos=0.20)),
        ("D nud 0.00", variante(base, nudillos=0.0)),
        ("E nud 0.20 spr suave", variante(base, nudillos=0.20, spreads=(-8, -3, 3, 8))),
        ("F nud 0.00 spr suave", variante(base, nudillos=0.0, spreads=(-8, -3, 3, 8))),
        ("G nud 0.20 spr 0", variante(base, nudillos=0.20, spreads=(0, 0, 0, 0))),
        ("H nud 0.00 spr 0", variante(base, nudillos=0.0, spreads=(0, 0, 0, 0))),
    ]
    if len(sys.argv) > 1:
        solo = set(sys.argv[1].upper())
        casos = [c for c in casos if c[0][0] in solo]

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        for nombre, pose in casos:
            aplicar(page, pose)
            m = page.evaluate(MED_JS)
            if "error" in m:
                raise SystemExit("medida fallida: " + m["error"])
            print(informe(nombre, m))
            print(detalle(m))
            retratar(page, viewer, nombre, OUT, salida)
        browser.close()

    for hoja in publicar(salida, OUT):
        print("hoja:", hoja)


if __name__ == "__main__":
    main()
