"""Da la vuelta a la mano para fijar la orientacion del marco de la palma.

Hace falta porque el signo de `frente` se deduce de la geometria del rig, y si
estuviera invertido todas las medidas de "delante/detras" mentirian. Con las
seis vistas en una hoja se ve de que lado esta la palma.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from lab_e2 import abrir, aplicar, preparar, publicar, retratar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "vueltas_e2"

VISTAS = {
    "1_frente": (1.0, 0.0, 0.0),
    "2_dorso": (-1.0, 0.0, 0.0),
    "3_pulgar": (0.0, 0.0, -1.0),
    "4_menique": (0.0, 0.0, 1.0),
    "5_arriba": (0.0, 1.0, 0.0),
    "6_abajo": (0.0, -1.0, 0.0),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    pose = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        aplicar(page, pose)
        for nombre, pesos in VISTAS.items():
            retratar(page, viewer, nombre, OUT, salida, vistas={"v": pesos})
        browser.close()

    # todas las vistas de la misma pose van a la misma lista
    hoja = {"vueltas": [(n, OUT / f"{n}_v.png") for n in VISTAS]}
    for p in publicar(hoja, OUT, cols=4, cell=300):
        print("hoja:", p)


if __name__ == "__main__":
    main()
