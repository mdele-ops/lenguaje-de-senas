"""Etapa 7 de la C: separacion entre dedos, para que el arco se lea como una sola banda."""
import itertools
from pathlib import Path

import c_lab
import lab
from c_lab import T1

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "ref_c" / "ref_c_original.png"
OUT = ROOT / "tools" / "screenshots" / "c_stage7"

SPREADS = {
    "s0": (0, 0, 0, 0),
    "s1": (4, 1, -1, -4),
    "s2": (8, 3, -3, -8),
    "sinv": (-4, -1, 1, 4),
}


def main():
    cases = {}
    for sname, mid in itertools.product(tuple(SPREADS), (34, 40)):
        cases[f"{sname}_m{mid}"] = c_lab.build(
            curl=0.26,
            knuckle=20,
            mid=mid,
            dist=12,
            tcurl=0.42,
            taside=0.8,
            thumb={T1: {"y": 34, "z": 8}},
            wy=90,
            wz=0,
            spread=SPREADS[sname],
        )

    rows = c_lab.run("c_stage7", cases, orbits=(0,), cols=3, cell=340, radius="0.32m")
    lab.sheet(
        [("REFERENCIA", REF)] + [(n, OUT / f"{n}.png") for n in cases],
        OUT / "_vs_referencia.png",
        cols=3,
        cell=340,
    )
    for r in sorted(rows, key=lambda x: x["score"]):
        print(f"{r['score']:.3f} juntos={r['juntos']:.2f} abertura={r['abertura']:.2f}  {r['caso']}")


if __name__ == "__main__":
    main()
