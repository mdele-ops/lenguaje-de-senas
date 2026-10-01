"""Vuelca las medidas guardadas de un barrido de la S, sin volver a renderizar.

Los barridos tardan minutos; cuando lo unico que hace falta es mirar otra
columna del resultado no merece la pena repetirlos.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COLS = (
    "camU", "camAlt", "camCima", "camDelante", "sobreFrente", "sobreFrenteIP",
    "freMax", "gapDedos", "apoyoIdx", "apoyoMed", "thLatDir", "thUpDir",
)


def main():
    ruta = ROOT / "tools" / "screenshots" / sys.argv[1] / "_top.json"
    cuantos = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    datos = json.loads(ruta.read_text("utf-8"))
    print(f"{'pose':26s}" + "".join(f"{c:>13s}" for c in COLS))
    for r in datos[:cuantos]:
        m = r["m"]
        fila = "".join(f"{m.get(c, float('nan')):+13.3f}" for c in COLS)
        print(f"{r['nombre'][:25]:26s}{fila}")


if __name__ == "__main__":
    main()
