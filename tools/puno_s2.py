"""S lab 7: cerrar el puno doblando SOLO los nudillos.

El lab 4 probo a doblar mas la falange media y salio al reves: a curl 1.0 esa
articulacion ya esta a 90 grados, de modo que los grados de mas la pasan de
rosca y la yema vuelve a subir. Lo que falta cerrar esta en el nudillo (MCP),
que a curl 1.0 se queda en 72 grados y deja el puno alto y abierto de frente.

Aqui se dobla solo el nudillo y se mira donde acaba la yema:
  puntaAlt    yema respecto a su nudillo, en palmas. Cuanto mas negativo, mas
              baja la yema hacia la base de la palma, que es lo que cierra el
              puno visto de frente.
  puntaPalma  yema -> muneca. Tiene que bajar, no subir.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import BONES, free_camera
from pose_lab_s import MEASURE_JS, pose_s
from puno_s import flexion
from ver_s import VISTAS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "puno_s2"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "ref_S_big.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s7"


def linea(nombre, m):
    return (
        f"{nombre:14s} puntaAlt={m['puntaAlt']:+.3f} puntaPalma={m['puntaPalma']:.3f} "
        f"puntaFre={m['puntaFre']:+.3f} freMax={m['freMax']:+.3f}"
    )


def main():
    casos = {}
    for prox in (0, 10, 20, 30, 40):
        pose = pose_s(cierre=1.0, tcurl=0.0)
        if prox:
            pose["extra"].update(flexion(prox=prox))
        casos[f"prox{prox}"] = pose
    # y con un punto menos de falange media, por si el puno queda demasiado
    # apretado y los dedos se meten dentro de la palma
    for prox in (20, 30):
        pose = pose_s(cierre=0.9, tcurl=0.0)
        pose["extra"].update(flexion(prox=prox))
        casos[f"c09_prox{prox}"] = pose

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        items = [("REF lamina", REF)] if REF.exists() else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            print(" ", linea(nombre, m))
            for vista, orbit in VISTAS[:2]:
                ruta = OUT / f"{nombre}_{vista}.png"
                cam(page, orbit)
                captura(page, ruta, MANO, margen=0.30)
                items.append((f"{nombre} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=5, cell=300, titulo="S · nudillos")
    (OUT / "_medidas.json").write_text(json.dumps(medidas, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
