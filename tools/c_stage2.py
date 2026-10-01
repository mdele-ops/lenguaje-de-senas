"""Etapa 2 de la C: con la muneca ya de perfil (wy=90), barrer el arco y el pulgar."""
import itertools
import json
from pathlib import Path

import c_lab
from c_lab import T1, T2

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "c_stage2"

THUMBS = {
    "tA": {T1: {"y": 34, "z": 8}},
    "tB": {T1: {"y": 20, "z": 22}},
    "tC": {T1: {"y": 46, "z": 0}},
    "tD": {T1: {"y": 34, "z": 8}, T2: {"x": -12}},
    "tE": {T1: {"y": 24, "z": 14}, T2: {"x": -20}},
}


def build_cases():
    cases = {}
    for curl, knuckle, mid, tcurl, taside, tname in itertools.product(
        (0.18, 0.26, 0.34),
        (20, 28, 36),
        (14, 24, 34),
        (0.18, 0.28, 0.38),
        (0.45, 0.7),
        tuple(THUMBS),
    ):
        name = f"c{curl}_k{knuckle}_m{mid}_tc{tcurl}_ta{taside}_{tname}"
        cases[name] = c_lab.build(
            curl=curl,
            knuckle=knuckle,
            mid=mid,
            tcurl=tcurl,
            taside=taside,
            thumb=THUMBS[tname],
            wy=90,
            wz=0,
        )
    return cases


def main():
    cases = build_cases()
    print("combinaciones:", len(cases))
    rows = c_lab.measure_all(cases)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ranking.json").write_text(
        json.dumps(rows[:60], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== mejores 25 ===")
    for r in rows[:25]:
        print(
            f"{r['score']:.3f} abertura={r['abertura']:.2f} cuerda={r['cuerda']:.2f} "
            f"juntos={r['juntos']:.2f} dy={r['dy']:+.2f} huecoX={r['hueco_x']:+.2f}  {r['caso']}"
        )


if __name__ == "__main__":
    main()
