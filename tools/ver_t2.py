"""T: finalistas en grande, con el esqueleto, y la S al lado como patron.

Se usa `mira_t.captura`, que recorta a la mano y dibuja los huesos DENTRO del
recorte. El punto rojo gordo es la yema del pulgar. Para que sea una T tiene
que caer en el hueco entre la cadena azul (indice) y la verde (medio), y por
encima de las dos.

Se mete tambien la S del catalogo: es la letra hermana y ya esta dada por
buena, asi que sirve de patron de "asi se ve un puno bien hecho en este render"
y de recordatorio de en que se tienen que diferenciar.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import hoja
from mira_t import abrir_nitido, captura
from pose_lab_e import free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
from ver_s import CAM_FOV, CAM_TARGET
from ver_t import ref_grande
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "ver_t2"
OUT.mkdir(parents=True, exist_ok=True)
TOP = ROOT / "tools" / "screenshots" / "search_t" / "_top.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t5"

VISTAS = (("frente", "0deg 84deg 2.5m"),
          ("arriba", "0deg 45deg 2.5m"))
CUANTAS = 6


def cam(page, orbit):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": orbit, "fov": CAM_FOV},
    )
    time.sleep(0.22)


def revisa(page, nombre, pose, items, medir=True):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.3)
    cam(page, VISTAS[0][1])
    if medir:
        m = page.evaluate(MEASURE_JS)
        print(" ", linea(nombre, m, puntua(m)[0]))
    for vista, orbit in VISTAS:
        cam(page, orbit)
        for sufijo, esq in (("", False), ("_esq", True)):
            ruta = OUT / f"{nombre}_{vista}{sufijo}.png"
            captura(page, ruta, esqueleto=esq, margen=0.24, lado=700)
            items.append((f"{nombre} {vista}{sufijo}", ruta))


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}
    top = json.loads(TOP.read_text("utf-8"))[:CUANTAS]

    with sync_playwright() as p:
        # a doble escala: el recorte sale de la captura, asi que manda la nitidez
        browser, page = abrir_nitido(p, lado=760, escala=2)
        free_camera(page)

        items = [("REF lamina", ref_grande(560))]
        revisa(page, "S_catalogo", por_letra["S"]["pose"], items)
        for i, cand in enumerate(top):
            revisa(page, f"{i:02d}", construye(cand["receta"]), items)

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=430,
         titulo="T · finalistas con esqueleto (rojo=pulgar, azul=indice, verde=medio)")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
