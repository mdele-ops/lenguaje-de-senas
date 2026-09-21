"""R lab 6: cuanto cruce hace falta para que la letra se lea de frente.

Las candidatas que salen bien puntuadas se ven casi iguales desde la camara de
produccion: los dos dedos se tapan y la R parece una D. El cruce existe en la
geometria pero no en la silueta.

Esto barre solo la cantidad de cruce lateral, dejando fijo el escalon de
profundidad, y pone al lado la U y la V del catalogo (los dos vecinos con los
que la R se puede confundir) para ver a partir de que valor la silueta deja de
leerse como U y empieza a leerse como R.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import DEDOS, MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from search_r import cruzar, puntuar
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "barrido_r"
OUT.mkdir(parents=True, exist_ok=True)
REF_MANO = ROOT / "tools" / "screenshots" / "ref_R_mano.png"
REF_DEDOS = ROOT / "tools" / "screenshots" / "ref_R_dedos.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=r6"

# escalon de profundidad fijo: el medio sale hacia la palma en el nudillo y la
# falange media lo vuelve a poner paralelo al indice
FONDO = dict(mx=20, mx2=-10, ix=-8, ix2=8)

BARRIDO = [
    (6, -6), (10, -10), (10, -18), (14, -14),
    (14, -22), (18, -18), (18, -26), (22, -22),
    (26, -26), (30, -30),
]


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        manos, dedos = [], []
        if REF_MANO.exists():
            manos.append(("REF lamina", REF_MANO))
            dedos.append(("REF lamina", REF_DEDOS))

        def tirar(nombre, pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:16s} s={puntuar(m):6.3f} "
                f"cruce={m['cruce']:+5.2f}/{m['crucePip']:+5.2f} "
                f"gap={m['gap']:.3f} frente={m['frenteMed']:+5.2f} "
                f"yemas={m['sepYemas']:.2f}"
            )
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            r1 = OUT / f"{nombre}_mano.png"
            captura(page, r1, MANO, margen=0.28)
            manos.append((nombre, r1))
            r2 = OUT / f"{nombre}_dedos.png"
            captura(page, r2, DEDOS, margen=0.45)
            dedos.append((nombre, r2))

        # vecinos con los que se confunde
        for letra in ("U", "V"):
            tirar(f"cat_{letra}", por_letra[letra]["pose"])
        tirar("cat_R_vieja", por_letra["R"]["pose"])

        for iz, mz in BARRIDO:
            tirar(f"iz{iz}_mz{mz}", cruzar(iz=iz, mz=mz, **FONDO))

        browser.close()

    hoja(manos, OUT / "_manos.png", cols=5, cell=320, titulo="R · barrido de cruce")
    hoja(dedos, OUT / "_dedos.png", cols=5, cell=320, titulo="R · dedos de cerca")


if __name__ == "__main__":
    main()
