"""Renderiza las letras del catalogo y arma una hoja de contactos para
compararlas contra la lamina de referencia del alfabeto LSM.

Uso:
    py tools/render_letters.py                 # todas las letras
    py tools/render_letters.py O P Q           # solo algunas
    py tools/render_letters.py --views O       # ademas de frente, perfil y 3/4

Las poses se aplican con applyTestPose (sin la transicion de 2 s de produccion)
leyendo data/catalogo-lsm.json, asi que la hoja siempre refleja el JSON en disco.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import lab

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "letters"

# "frente" es el punto de vista del espectador, que es el que usa la lamina de
# referencia. El objetivo de camara se recalcula por pose dentro de lab.shot.
VIEWS = {
    "frente": f"0deg 84deg {lab.RADIUS}",
    "perfil": f"70deg 84deg {lab.RADIUS}",
    "tresq": f"35deg 78deg {lab.RADIUS}",
}

SAFE = {"Ñ": "N_", "○": "NEUTRAL"}


def safe_name(letra):
    return SAFE.get(letra, letra)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    multi_view = "--views" in sys.argv
    wanted = {a.upper() for a in args} if args else None

    catalog = lab.load_catalog()
    senas = catalog["senas"]
    if wanted:
        senas = [s for s in senas if s["letra"].upper() in wanted]
    if not senas:
        print("No hay letras que coincidan.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    views = VIEWS if multi_view else {"frente": VIEWS["frente"]}

    with sync_playwright() as p:
        browser = p.chromium.launch(args=lab.CHROME_ARGS)
        page = lab.open_lab(browser, catalog)

        for view_name, orbit in views.items():
            shots = []
            for sena in senas:
                letra = sena["letra"]
                lab.apply_pose(page, sena.get("pose"))
                out = OUT_DIR / f"{view_name}_{safe_name(letra)}.png"
                lab.shot(page, out, orbit=orbit)
                shots.append((letra, out))
                print("  ", view_name, letra)
            lab.sheet(shots, OUT_DIR / f"_hoja_{view_name}.png", cols=6, cell=240)

        browser.close()


if __name__ == "__main__":
    main()
