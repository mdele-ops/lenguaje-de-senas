"""Tercera pasada de la E: poner las cuatro yemas en la misma fila.

Con los nudillos ya sueltos el puno se lee, pero las yemas bajan en escalera
del indice al menique. `largo` no sirve para subirlas: los cuatro dedos estan
sobre-enrollados (mas de 240 grados), asi que alargar la falange manda la yema
mas abajo. Lo que las mueve es el `curl`, y aqui se mide cuanto.
"""
import copy
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from e2_medidas import MED_JS
from lab_e2 import abrir, aplicar, preparar, publicar, retratar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "fila_e"

FINGERS = ("index", "middle", "ring", "pinky")


def variante(base, curls, largo=None):
    p = copy.deepcopy(base)
    for finger, c in zip(FINGERS, curls):
        p[finger]["curl"] = c
    if largo is not None:
        p["largo"] = dict(largo)
    return p


def _f(vals):
    return "[" + " ".join(f"{v:+.3f}" for v in vals) + "]"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    base = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    casos = [
        ("A actual", variante(base, (0.78, 0.98, 0.96, 0.98))),
        ("B pky/ring -", variante(base, (0.78, 0.98, 0.90, 0.88))),
        ("C pky/ring --", variante(base, (0.78, 0.98, 0.86, 0.82))),
        ("D ind 0.70", variante(base, (0.70, 0.98, 0.96, 0.98))),
        ("E ind.70 pky/ring -", variante(base, (0.70, 0.94, 0.90, 0.88))),
        ("F ind.74 mid.94 rng.88 pky.84", variante(base, (0.74, 0.94, 0.88, 0.84))),
        ("G largo 1", variante(base, (0.78, 0.98, 0.96, 0.98), {})),
        ("H F sin largo", variante(base, (0.74, 0.94, 0.88, 0.84), {})),
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
            print(
                f"{nombre:32s} alto={_f(m['alto'])} D={m['altoDisp']:.3f} "
                f"yemaRel={_f(m['yemaRel'])} D={m['yemaRelDisp']:.3f} "
                f"gaps={_f(m['gaps'])} toca={m['tocaDedos']:.2f} tipoI={m['tipoI']:.2f}"
            )
            retratar(page, viewer, nombre, OUT, salida)
        browser.close()

    for h in publicar(salida, OUT):
        print("hoja:", h)


if __name__ == "__main__":
    main()
