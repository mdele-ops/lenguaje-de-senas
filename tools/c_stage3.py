"""Etapa 3 de la C: fotografia los mejores candidatos de la etapa 2 junto a la referencia."""
import json
from pathlib import Path

import c_lab
import lab
from c_lab import T1, T2

ROOT = Path(__file__).resolve().parents[1]
RANKING = ROOT / "tools" / "screenshots" / "c_stage2" / "ranking.json"
REF = ROOT / "tools" / "screenshots" / "ref_c" / "ref_c_original.png"
OUT = ROOT / "tools" / "screenshots" / "c_stage3"

THUMBS = {
    "tA": {T1: {"y": 34, "z": 8}},
    "tB": {T1: {"y": 20, "z": 22}},
    "tC": {T1: {"y": 46, "z": 0}},
    "tD": {T1: {"y": 34, "z": 8}, T2: {"x": -12}},
    "tE": {T1: {"y": 24, "z": 14}, T2: {"x": -20}},
}


def parse(caso):
    """c0.34_k20_m24_tc0.38_ta0.7_tA -> kwargs de c_lab.build"""
    parts = caso.split("_")
    return {
        "curl": float(parts[0][1:]),
        "knuckle": int(parts[1][1:]),
        "mid": int(parts[2][1:]),
        "tcurl": float(parts[3][2:]),
        "taside": float(parts[4][2:]),
        "thumb": THUMBS[parts[5]],
    }


def main():
    rows = json.loads(RANKING.read_text(encoding="utf-8"))
    top = rows[:14]
    cases = {}
    for i, r in enumerate(top):
        cases[f"{i:02d}_{r['caso']}"] = c_lab.build(wy=90, wz=0, **parse(r["caso"]))

    c_lab.run("c_stage3", cases, orbits=(0,), cols=5, cell=250)

    shots = [("REFERENCIA", REF)] + [
        (name, OUT / f"{name}.png") for name in cases
    ]
    lab.sheet(shots, OUT / "_vs_referencia.png", cols=5, cell=250)


if __name__ == "__main__":
    main()
