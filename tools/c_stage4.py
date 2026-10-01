"""Etapa 4 de la C: reparte el arco entre nudillo, falange media y distal."""
import itertools
from pathlib import Path

import c_lab
import lab
from c_lab import T1, T2

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "ref_c" / "ref_c_original.png"
OUT = ROOT / "tools" / "screenshots" / "c_stage4"

THUMBS = {
    "recto": {T1: {"y": 34, "z": 8}},
    "curvo": {T1: {"y": 40, "z": 4}, T2: {"x": -14}},
}


def main():
    cases = {}
    for knuckle, mid, dist, tname in itertools.product(
        (20, 30), (30, 38), (0, 14, 26), tuple(THUMBS)
    ):
        name = f"k{knuckle}_m{mid}_d{dist}_{tname}"
        cases[name] = c_lab.build(
            curl=0.26,
            knuckle=knuckle,
            mid=mid,
            dist=dist,
            tcurl=0.38,
            taside=0.7,
            thumb=THUMBS[tname],
            wy=90,
            wz=0,
        )

    print("combinaciones:", len(cases))
    rows = c_lab.run("c_stage4", cases, orbits=(0,), cols=5, cell=250)

    shots = [("REFERENCIA", REF)] + [(n, OUT / f"{n}.png") for n in cases]
    lab.sheet(shots, OUT / "_vs_referencia.png", cols=5, cell=250)

    print("\n=== orden por score ===")
    for r in rows:
        print(
            f"{r['score']:.3f} abertura={r['abertura']:.2f} cuerda={r['cuerda']:.2f} "
            f"dy={r['dy']:+.2f}  {r['caso']}"
        )


if __name__ == "__main__":
    main()
