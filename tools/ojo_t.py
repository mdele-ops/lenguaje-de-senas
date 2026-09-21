"""T: la mano a tamano real, para ver si el pulgar asoma de verdad.

Las hojas anteriores dejaban una duda seria: el esqueleto dice que la yema del
pulgar esta arriba y entre indice y medio, pero en el render no se ve ningun
pulgar. O la malla se queda enterrada dentro de la mano, o es que la imagen
estaba tan ampliada que no se distinguia. Aqui se quita esa duda acercando la
camara a 40 cm: el recorte deja de ser una ampliacion y sale con pixeles
reales.

Se saca cada pose con y sin esqueleto y en dos vistas, y se mete la S del
catalogo como patron.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import hoja
from mira_t import acerca, captura
from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
from ver_t import ref_grande
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "ojo_t"
OUT.mkdir(parents=True, exist_ok=True)
TOP = ROOT / "tools" / "screenshots" / "search_t" / "_top.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t6"

CERCA = (("frente", "0deg 84deg 0.40m"),
         ("arriba", "0deg 40deg 0.40m"))


def prod(page):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
    )
    time.sleep(0.22)


def revisa(page, nombre, pose, items):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.3)
    prod(page)
    m = page.evaluate(MEASURE_JS)
    print(" ", linea(nombre, m, puntua(m)[0]))
    hand = page.evaluate(HAND_POS_JS)
    for vista, orbit in CERCA:
        acerca(page, hand, orbit)
        for sufijo, esq in (("", False), ("_esq", True)):
            ruta = OUT / f"{nombre}_{vista}{sufijo}.png"
            captura(page, ruta, esqueleto=esq, margen=0.20, lado=560)
            items.append((f"{nombre} {vista}{sufijo}", ruta))
    return m


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}
    top = json.loads(TOP.read_text("utf-8"))[:4]

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1400, "height": 1400})
        time.sleep(0.5)
        free_camera(page)

        items = [("REF lamina", ref_grande(560))]
        revisa(page, "S_catalogo", por_letra["S"]["pose"], items)
        for i, cand in enumerate(top):
            revisa(page, f"{i:02d}", construye(cand["receta"]), items)

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=430,
         titulo="T · tamano real (rojo=pulgar, azul=indice, verde=medio)")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
