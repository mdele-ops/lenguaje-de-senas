"""Barrido corto alrededor de un candidato, para rematarlo mirando.

Las medidas no bastan para dar el ultimo paso: aciertan la forma, pero entre
dos poses con casi la misma puntuacion la que se parece a la lamina se decide
comparando renders. Aqui se parte de un candidato de `busca_pulgar_e` y se
mueven dos mandos alrededor suyo.

`tcurl` y el cierre del nudillo (`t2x`) son los que regulan cuanto CRUZA el
pulgar: con el pulgar ya horizontal, subirlos alarga la barra y la punta acaba
asomando por el borde del menique.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_e import calibrar, pose, pulgar
from hoja_e import preparar, publicar, retratar
from pose_lab_e import T1, T3
from pulgar_e import PULGAR_JS
from pulgar_e import linea as linea_pulgar
from pulgar_e import puntuar as puntuar_pulgar
from search_e9 import abrir
from search_e10 import CAM_PROD_JS
from simetria_e import SIMETRIA_JS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "escalera_pulgar_e"
BUSQUEDA = ROOT / "tools" / "screenshots" / "busca_pulgar_e.json"

DEDOS = {"mcp": 70.0, "pip": 95.0, "dip": 90.0}
CONV = 8

VISTAS = {
    "frente": ("0deg 84deg 0.95m", "22deg"),
    "lado": ("-62deg 84deg 0.95m", "22deg"),
}

BASE = 1  # indice del candidato de busca_pulgar_e del que se parte
PASOS = [(tc, t2x) for tc in (0.40, 0.50, 0.59) for t2x in (8, 16, 24, 32)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = json.loads(BUSQUEDA.read_text("utf-8"))["mejores"][BASE]["pulgar"]
    aside = base["aside"]
    t1 = base.get(T1, {})
    t3x = base.get(T3, {}).get("x", 0)

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        def sim(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            return page.evaluate(SIMETRIA_JS)

        corr, _ = calibrar(sim, 0.0, CONV, objetivo=DEDOS, verbose=False)

        salida, registro = {}, {}
        for tc, t2x in PASOS:
            th = pulgar(
                tc, aside,
                t1={"x": t1.get("x", 0), "y": t1.get("y", 0), "z": t1.get("z", 0)},
                t2={"x": t2x},
                t3={"x": t3x},
            )
            pz = pose(0.0, CONV, corr, th)
            sim(pz)
            page.evaluate(CAM_PROD_JS)
            m = page.evaluate(PULGAR_JS)
            nombre = f"c{int(tc * 100):02d}_mp{t2x:02d}"
            print(linea_pulgar(nombre, m, puntuar_pulgar(m)))
            registro[nombre] = {"pose": pz, "pulgar": th, "m": m}
            retratar(page, viewer, nombre, OUT, salida, vistas=VISTAS, app=False)
        browser.close()

    publicar(salida, OUT, cols=6, cell=290)
    (OUT / "_escalera.json").write_text(json.dumps(registro, indent=2), "utf-8")


if __name__ == "__main__":
    main()
