"""Comprueba que la C nueva convive con sus vecinas y no arrastra rotaciones."""
from pathlib import Path

from playwright.sync_api import sync_playwright

import c_lab
import lab

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "c_vecinas"

# Se pasa por la C en medio de las vecinas para detectar rotaciones que se queden
# pegadas de una letra a la siguiente.
SECUENCIA = ["B", "C", "D", "C", "E", "C", "O"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = lab.load_catalog()
    poses = {s["letra"]: s.get("pose") for s in catalog["senas"]}

    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        shots = []
        for i, letra in enumerate(SECUENCIA):
            lab.apply_pose(page, poses[letra])
            out = OUT / f"{i}_{letra}.png"
            lab.shot(page, out, orbit="0deg 84deg 0.34m", side="right")
            shots.append((f"{i}. {letra}", out))
            print("  ", letra, flush=True)
        browser.close()

    lab.sheet(shots, OUT / "_hoja.png", cols=4, cell=300)


if __name__ == "__main__":
    main()
