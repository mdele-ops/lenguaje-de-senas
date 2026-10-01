"""Etapa 6 de la C: el pulgar opuesto que cierra el arco por abajo.

Los cuatro dedos quedan fijos en el arco ganador de la etapa 5.
"""
import itertools
from pathlib import Path

import c_lab
import lab
from c_lab import T1, T2, T3

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "ref_c" / "ref_c_original.png"
OUT = ROOT / "tools" / "screenshots" / "c_stage6"

THUMBS = {
    "base": {T1: {"y": 34, "z": 8}},
    "arriba": {T1: {"y": 34, "z": -12}},
    "arriba2": {T1: {"y": 28, "z": -26}},
    "afuera": {T1: {"y": 50, "z": 0}},
    "curvo": {T1: {"y": 34, "z": 8}, T2: {"x": -16}},
    "curvo2": {T1: {"y": 34, "z": -10}, T2: {"x": -16}},
    "punta": {T1: {"y": 34, "z": -6}, T3: {"x": -18}},
    "opuesto": {T1: {"y": 40, "z": -8, "x": 12}},
    "opuesto2": {T1: {"y": 30, "z": -18, "x": 18}},
}


def main():
    cases = {}
    for tcurl, tname in itertools.product((0.28, 0.42), tuple(THUMBS)):
        cases[f"tc{tcurl}_{tname}"] = c_lab.build(
            curl=0.26,
            knuckle=20,
            mid=34,
            dist=12,
            tcurl=tcurl,
            taside=0.8,
            thumb=THUMBS[tname],
            wy=90,
            wz=0,
        )

    print("combinaciones:", len(cases))
    rows = c_lab.run("c_stage6", cases, orbits=(0,), cols=5, cell=300, radius="0.34m")

    shots = [("REFERENCIA", REF)] + [(n, OUT / f"{n}.png") for n in cases]
    lab.sheet(shots, OUT / "_vs_referencia.png", cols=5, cell=300)

    for r in sorted(rows, key=lambda x: x["score"]):
        print(
            f"{r['score']:.3f} abertura={r['abertura']:.2f} dy={r['dy']:+.2f} "
            f"huecoX={r['hueco_x']:+.2f}  {r['caso']}"
        )


if __name__ == "__main__":
    main()
