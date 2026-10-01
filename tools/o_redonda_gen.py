"""Genera candidatos para o_redonda.py a partir de la C, cerrando los dedos."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_redonda"

cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text(encoding="utf-8"))
S = {s["letra"]: s["pose"] for s in cat["senas"]}
DEDOS = ("Index", "Middle", "Ring", "Pinky")


def pose(k1, k2, k3, t1, t2, tcurl, aside, spread=(4, 1, -1, -4), muneca=None):
    p = copy.deepcopy(S["C"])
    for f, sp in zip(("index", "middle", "ring", "pinky"), spread):
        p[f] = {"curl": 0.26, "spread": sp}
    for f in DEDOS:
        p["extra"][f"RightHand{f}1"] = {"x": k1}
        p["extra"][f"RightHand{f}2"] = {"x": k2}
        p["extra"][f"RightHand{f}3"] = {"x": k3}
    p["thumb"] = {"curl": tcurl, "aside": aside}
    p["extra"]["RightHandThumb1"] = dict(t1)
    p["extra"]["RightHandThumb2"] = {"x": t2}
    if muneca:
        p["muneca"] = muneca
    return p


def forma(curl=0.6, extra2=16, nud=0.3):
    p = copy.deepcopy(S["O"])
    for f, sp in zip(("index", "middle", "ring", "pinky"), (4, 1, -2, -5)):
        p[f] = {"curl": curl, "spread": sp}
    for f in DEDOS:
        p["extra"][f"RightHand{f}1"] = {"x": 24}
        p["extra"][f"RightHand{f}2"] = {"x": extra2}
        p["extra"][f"RightHand{f}3"] = {"x": -10}
    if nud:
        p["nudillos"] = nud
    return p


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "a"
    c = {"O_actual": S["O"], "C_actual": S["C"]}
    if modo == "a":
        for k1 in (30, 42):
            for k2 in (45, 60):
                for tx in (-30, -15):
                    c[f"k{k1}_{k2}_tx{tx}"] = pose(
                        k1, k2, 20, {"x": tx, "y": 34, "z": 25}, -20, 0.5, 0.8
                    )
    if modo == "b":
        for curl in (0.6, 0.7):
            for extra2 in (6, 16):
                for nud in (0, 0.3):
                    p = copy.deepcopy(S["O"])
                    for f, sp in zip(("index", "middle", "ring", "pinky"), (4, 1, -2, -5)):
                        p[f] = {"curl": curl, "spread": sp}
                    for f in DEDOS:
                        p["extra"][f"RightHand{f}1"] = {"x": 24}
                        p["extra"][f"RightHand{f}2"] = {"x": extra2}
                        p["extra"][f"RightHand{f}3"] = {"x": -10}
                    if nud:
                        p["nudillos"] = nud
                    c[f"c{curl}_e{extra2}_n{nud}"] = p
    if modo == "m":
        c = {}
        base = forma()
        for x in (-15, 15, 45):
            for y in (70, 100, 130):
                for z in (-50, -20, 10):
                    p = copy.deepcopy(base)
                    p["muneca"] = {"x": x, "y": y, "z": z}
                    c[f"x{x}_y{y}_z{z}"] = p
    if modo == "t":
        c = {}
        for curl in (0.6, 0.7):
            for t1z in (40, 55):
                for t2 in (35, 55):
                    for t1x in (-8, 10):
                        p = forma(curl=curl)
                        p["muneca"] = {"x": 15, "y": 70, "z": -50}
                        p["extra"]["RightHandThumb1"] = {"x": t1x, "y": -28, "z": t1z}
                        p["extra"]["RightHandThumb2"] = {"x": t2}
                        c[f"c{curl}_z{t1z}_t{t2}_x{t1x}"] = p
    if modo == "t":
        c = {}
        for curl in (0.6, 0.7):
            for t1z in (40, 55):
                for t2 in (35, 55):
                    for t1x in (-8, 10):
                        p = forma(curl=curl)
                        p["muneca"] = {"x": 15, "y": 70, "z": -50}
                        p["extra"]["RightHandThumb1"] = {"x": t1x, "y": -28, "z": t1z}
                        p["extra"]["RightHandThumb2"] = {"x": t2}
                        c[f"c{curl}_z{t1z}_t{t2}_x{t1x}"] = p
    if modo == "v":
        c = {}
        actual = S["O"]
        for x in (-40, -15, 15):
            for y in (50, 70, 90):
                for z in (-50, -20, 10, 40):
                    p = copy.deepcopy(actual)
                    p["muneca"] = {"x": x, "y": y, "z": z}
                    c[f"x{x}_y{y}_z{z}"] = p
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "candidatos.json").write_text(json.dumps(c, indent=1), encoding="utf-8")
    print(len(c), "candidatos")


if __name__ == "__main__":
    main()
