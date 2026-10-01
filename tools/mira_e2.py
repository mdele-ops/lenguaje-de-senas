"""Retrata la E del catalogo al lado de la foto de referencia.

No cambia nada: solo mide y saca la hoja de contactos para ver que dedo esta
fuera de sitio antes de tocar la pose.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from e2_medidas import MED_JS, detalle, informe
from lab_e2 import abrir, aplicar, preparar, publicar, retratar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "mira_e2"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    pose = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        aplicar(page, pose)

        m = page.evaluate(MED_JS)
        if "error" in m:
            raise SystemExit("medida fallida: " + m["error"])
        print(informe("E catalogo", m))
        print(detalle(m))
        retratar(page, viewer, "catalogo", OUT, salida)
        browser.close()

    for hoja in publicar(salida, OUT):
        print("hoja:", hoja)


if __name__ == "__main__":
    main()
