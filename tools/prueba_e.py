"""Banco de pruebas de la E: se le pasan candidatas y devuelve hojas y medidas.

Es el script que se edita para cada ronda. Las dos cosas que quedan por decidir
despues de calibrar los dedos son la convergencia (que los dedos se toquen, como
en la foto, sin atravesarse) y el pulgar (que quede plegado contra la palma y no
asomando por el borde de la mano).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_e import PULGAR, calibrar, pose, pulgar
from hoja_e import preparar, publicar, retratar
from pulgar_e import PULGAR_JS
from pulgar_e import linea as linea_pulgar
from pulgar_e import puntuar as puntuar_pulgar
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, informe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "prueba_e"
BUSQUEDA = ROOT / "tools" / "screenshots" / "busca_pulgar_e.json"

DEDOS = {"mcp": 70.0, "pip": 95.0, "dip": 90.0}
CONV = 8

VISTAS = {
    "frente": ("0deg 84deg 0.95m", "22deg"),
    "lado": ("-62deg 84deg 0.95m", "22deg"),
}


def candidatas(mejores):
    """(nombre, conv, pulgar) por candidata."""
    casos = [("dedos_solo", CONV, PULGAR)]
    for i, item in enumerate(mejores[:8]):
        casos.append((f"pulgar{i}", CONV, item["pulgar"]))
    return casos


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]
    mejores = json.loads(BUSQUEDA.read_text("utf-8"))["mejores"]

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        def aplicar(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)

        def sim(pz):
            aplicar(pz)
            return page.evaluate(SIMETRIA_JS)

        salida = {}
        s = sim(actual)
        m = page.evaluate(PULGAR_JS)
        print(informe("0_actual", s))
        print("  ", linea_pulgar("0_actual", m, puntuar_pulgar(m)))
        retratar(page, viewer, "0_actual", OUT, salida, vistas=VISTAS, app=True)

        registro = {}
        cache = {}
        for nombre, conv, th in candidatas(mejores):
            if conv not in cache:
                cache[conv] = calibrar(
                    sim, 0.0, conv, objetivo=DEDOS, verbose=False
                )[0]
            corr = cache[conv]
            pz = pose(0.0, conv, corr, th)
            s = sim(pz)
            m = page.evaluate(PULGAR_JS)
            print(informe(nombre, s))
            print("  ", linea_pulgar(nombre, m, puntuar_pulgar(m)))
            registro[nombre] = {"pose": pz, "simetria": s, "pulgar": m}
            retratar(page, viewer, nombre, OUT, salida, vistas=VISTAS, app=True)
        browser.close()

    publicar(salida, OUT, cols=5, cell=290)
    (OUT / "_candidatas.json").write_text(json.dumps(registro, indent=2), "utf-8")


if __name__ == "__main__":
    main()
