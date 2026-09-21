"""Etapa 5 de la C: inclinacion de la muneca (wz) y forma del pulgar, encuadre cerrado."""
import itertools
from pathlib import Path

import c_lab
import lab
from c_lab import T1, T2

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "ref_c" / "ref_c_original.png"
OUT = ROOT / "tools" / "screenshots" / "c_stage5"

THUMBS = {
    "recto": {T1: {"y": 34, "z": 8}},
    "curvo": {T1: {"y": 40, "z": 4}, T2: {"x": -14}},
}


def main():
    cases = {}
    for wz, dist, tname in itertools.product((0, 12, 25), (0, 12), tuple(THUMBS)):
        cases[f"wz{wz}_d{dist}_{tname}"] = c_lab.build(
            curl=0.26,
            knuckle=20,
            mid=34,
            dist=dist,
            tcurl=0.34,
            taside=0.7,
            thumb=THUMBS[tname],
            wy=90,
            wz=wz,
        )

    print("combinaciones:", len(cases))
    rows = c_lab.run("c_stage5", cases, orbits=(0,), cols=4, cell=330, radius="0.34m")

    shots = [("REFERENCIA", REF)] + [(n, OUT / f"{n}.png") for n in cases]
    lab.sheet(shots, OUT / "_vs_referencia.png", cols=4, cell=330)

    for r in sorted(rows, key=lambda x: x["score"]):
        print(
            f"{r['score']:.3f} abertura={r['abertura']:.2f} cuerda={r['cuerda']:.2f} "
            f"dedosY={r['dedos_y']:.2f} dy={r['dy']:+.2f}  {r['caso']}"
        )


if __name__ == "__main__":
    main()
