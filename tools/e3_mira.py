"""Retrata las candidatas de la E al lado de la foto, con la mano llenando el cuadro.

Uso: `python _run.py e3_mira.py [etiqueta]`, donde la etiqueta elige el lote de
poses de `LOTES`. Sin argumento sale el lote `base`.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from e2_medidas import MED_JS
from e3_barrido import linea_dedos, linea_pulgar
from e3_lab import pose_e, probar, publicar
from lab_e2 import abrir, preparar

ROOT = Path(__file__).resolve().parents[1]

BASE = {"nudillos": 0.45}

LOTES = {
    "base": [
        ("catalogo", pose_e()),
        ("nud 0.35", pose_e(nudillos=0.35)),
        ("nud 0.55", pose_e(nudillos=0.55)),
    ],
    # El pulgar del catalogo queda de pie y metido detras de los dedos (frente
    # negativo): no se ve nada. Estas variantes lo van tumbando sobre la palma.
    "pulgar1": [
        ("catalogo", pose_e(**BASE)),
        ("A t1 20/-10/30 t2 50", pose_e(t1=(20, -10, 30), t2x=50, **BASE)),
        ("B t1 20/-10/50 t2 50", pose_e(t1=(20, -10, 50), t2x=50, **BASE)),
        ("C t1 20/-10/70 t2 50", pose_e(t1=(20, -10, 70), t2x=50, **BASE)),
        ("D t1 20/-35/30 t2 50", pose_e(t1=(20, -35, 30), t2x=50, **BASE)),
        ("E t1 20/-10/30 t2 30", pose_e(t1=(20, -10, 30), t2x=30, **BASE)),
        ("F t1 20/-60/30 t2 50", pose_e(t1=(20, -60, 30), t2x=50, **BASE)),
    ],
}


def main():
    etiqueta = sys.argv[1] if len(sys.argv) > 1 else "base"
    lote = LOTES[etiqueta]
    out = ROOT / "tools" / "screenshots" / f"e3_{etiqueta}"
    out.mkdir(parents=True, exist_ok=True)

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        for nombre, pose in lote:
            m = probar(page, viewer, nombre, pose, out, salida, medir=MED_JS)
            print(linea_dedos(nombre, m))
            print("   ", linea_pulgar("", m).strip())
        browser.close()

    for hecha in publicar(salida, out, cols=min(4, len(lote) + 1)):
        print("hoja:", hecha)


if __name__ == "__main__":
    main()
