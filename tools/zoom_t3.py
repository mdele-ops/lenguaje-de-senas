"""T: primer plano de las finalistas, con y sin el esqueleto encima.

En la hoja de contactos de `ver_t.py` la mano sale a 520 px sacados de un
render de 1100, o sea muy blanda: no se distingue el pulgar del indice y no se
puede decidir nada. Aqui la camara se pega a la mano (orbit 0.55 m) y ademas se
dibuja el esqueleto proyectado, que es la unica forma segura de saber cual de
los bultos es el pulgar.

El punto rojo grande es la yema del pulgar: si no cae en el hueco entre el
azul (indice) y el verde (medio), y por encima de ellos, no es una T.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import hoja
from overlay_e import PROJECT_JS, dibujar_overlay, nombres_huesos
from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
from ver_t import ref_grande
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "zoom_t"
OUT.mkdir(parents=True, exist_ok=True)
TOP = ROOT / "tools" / "screenshots" / "search_t" / "_top.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t4"

CAM_PROD = ("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
# Vistas de cerca. La de frente es la que manda; la de arriba dice si el pulgar
# esta METIDO entre los dedos o solo puesto delante.
CERCA = (("frente", "0deg 84deg 0.55m"),
         ("arriba", "0deg 42deg 0.55m"))
CUANTAS = 6


def cam(page, target, orbit, fov="26deg"):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": target, "orbit": orbit, "fov": fov},
    )
    time.sleep(0.25)


def dispara(page, ruta, con_esqueleto):
    page.evaluate(
        "() => new Promise((r) => requestAnimationFrame("
        "() => requestAnimationFrame(r)))"
    )
    page.query_selector("#handViewer").screenshot(path=str(ruta))
    if con_esqueleto:
        datos = page.evaluate(PROJECT_JS, nombres_huesos())
        if not datos.get("error"):
            dibujar_overlay(ruta, datos["pts"], ruta)
    return ruta


def revisa(page, nombre, pose, items, medir=True):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.3)
    if medir:
        cam(page, *CAM_PROD)
        m = page.evaluate(MEASURE_JS)
        print(" ", linea(nombre, m, puntua(m)[0]))
    hand = page.evaluate(HAND_POS_JS)
    target = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
    for vista, orbit in CERCA:
        cam(page, target, orbit)
        for sufijo, esq in (("", False), ("_esq", True)):
            ruta = OUT / f"{nombre}_{vista}{sufijo}.png"
            dispara(page, ruta, esq)
            items.append((f"{nombre[:14]} {vista}{sufijo}", ruta))


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}
    top = json.loads(TOP.read_text("utf-8"))[:CUANTAS]

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        items = [("REF lamina", ref_grande(600))]
        # la S ya terminada, como patron de "esto si esta bien"
        revisa(page, "SS_catalogo", por_letra["S"]["pose"], items)
        for i, cand in enumerate(top):
            revisa(page, f"{i:02d}", construye(cand["receta"]), items)

        browser.close()

    hoja(items, OUT / "_finalistas.png", cols=4, cell=430,
         titulo="T · primer plano + esqueleto (rojo = pulgar)")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
