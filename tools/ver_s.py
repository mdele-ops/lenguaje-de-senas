"""S lab 2: ver en pantalla lo que dicen los numeros del lab 1.

El lab 1 deja claro que la S de hoy tiene el pulgar 0.89 palmas por DEBAJO de
las falanges medias (alt=-0.89): en vez de cruzar por delante de los dedos se
descuelga por la palma hacia la muneca. Pero antes de fijar rangos hay que
mirar los renders, porque el signo de la normal de la palma se hereda de los
labs anteriores y conviene comprobar a ojo hacia donde es "delante".

Se pintan las candidatas al lado de la lamina, siempre con el mismo recorte
(enfoque_r.captura) para que se puedan comparar.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, free_camera
from pose_lab_s import MEASURE_JS, linea, pose_s
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "ver_s"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "ref_S_big.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s2"

CAM_TARGET = "0m 2.45m 0.15m"
CAM_ORBIT = "0deg 84deg 2.5m"
CAM_FOV = "30deg"

# Tres angulos: de frente (lo que ve el usuario), de perfil por el lado del
# pulgar y desde arriba, que es donde se ve si el pulgar cruza o se hunde.
VISTAS = (("frente", "0deg 84deg 2.5m"),
          ("perfil", "-70deg 84deg 2.5m"),
          ("arriba", "0deg 45deg 2.5m"))


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
    time.sleep(0.2)


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    casos = {
        "S_actual": por_letra["S"]["pose"],
        "A_actual": por_letra["A"]["pose"],
        "base": pose_s(),
        # el pulgar llevado de lado con el eje z del nudillo, que es el que
        # mas lo cruza segun el lab 1
        "T1_z45": pose_s(tcurl=0.4, thumb={T1: {"z": 45}}),
        "T1_z60": pose_s(tcurl=0.4, thumb={T1: {"z": 60}}),
        "T2_z60": pose_s(tcurl=0.4, thumb={T2: {"z": 60}}),
        # y con el eje x, que lo baja
        "T1_x60": pose_s(tcurl=0.4, thumb={T1: {"x": 60}}),
        # combinaciones de partida
        "z50_x20": pose_s(tcurl=0.4, thumb={T1: {"z": 50, "x": 20}}),
        "z50_y-30": pose_s(tcurl=0.4, thumb={T1: {"z": 50, "y": -30}}),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        items = [("REF lamina", REF)] if REF.exists() else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            print(" ", linea(nombre, page.evaluate(MEASURE_JS)))
            for vista, orbit in VISTAS:
                cam(page, orbit)
                ruta = OUT / f"{nombre}_{vista}.png"
                captura(page, ruta, MANO, margen=0.30)
                items.append((f"{nombre} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=300, titulo="S · candidatas")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
