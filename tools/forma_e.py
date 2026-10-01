"""Cuanto tiene que doblar cada articulacion para que la E se lea como la foto.

Todas las candidatas salen ya calibradas (los cuatro dedos con los mismos
angulos), asi que la comparacion es limpia: lo unico que cambia entre celdas es
el reparto mcp/pip/dip.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_e import calibrar
from hoja_e import anotar, preparar, publicar, retratar
from search_e9 import abrir
from simetria_e import SIMETRIA_JS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "forma_e"

CASOS = {
    "a_45_95_60": (45, 95, 60),
    "b_55_95_60": (55, 95, 60),
    "c_65_95_60": (65, 95, 60),
    "d_75_95_60": (75, 95, 60),
    "e_65_105_55": (65, 105, 55),
    "f_65_85_70": (65, 85, 70),
    "g_75_105_45": (75, 105, 45),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        def ev(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            return page.evaluate(SIMETRIA_JS)

        salida = {}
        anotar("0_actual", ev(actual))
        retratar(page, viewer, "0_actual", OUT, salida)

        registro = {}
        for nombre, (mcp, pip, dip) in CASOS.items():
            corr, s = calibrar(
                ev, 0.0, -4,
                objetivo={"mcp": mcp, "pip": pip, "dip": dip},
                verbose=False,
            )
            anotar(nombre, s)
            registro[nombre] = {"objetivo": [mcp, pip, dip], "correcciones": corr}
            retratar(page, viewer, nombre, OUT, salida)
        browser.close()

    publicar(salida, OUT, cols=4, cell=300)
    (OUT / "_correcciones.json").write_text(json.dumps(registro, indent=2), "utf-8")


if __name__ == "__main__":
    main()
