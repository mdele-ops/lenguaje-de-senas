"""Hoja de contactos para candidatas de la E, con los dedos ya calibrados.

Se le pasa un diccionario {nombre: kwargs de calibra_e.calibrar} y devuelve las
hojas por vista. Cada candidata se calibra antes de retratarla, asi que todas
llegan con los cuatro dedos doblando lo mismo y lo unico que cambia es lo que
se quiso comparar.
"""
import time
from pathlib import Path

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from pose_lab_e import free_camera
from search_e10 import CAM_PROD_JS
from simetria_e import informe

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "referencia"

VISTAS = {
    "frente": ("0deg 84deg 0.95m", "22deg"),
    "lado": ("-62deg 84deg 0.95m", "22deg"),
    "abajo": ("0deg 112deg 0.95m", "22deg"),
}

REFERENCIAS = [("REF foto", REF / "E_usuario2.png")]


def encuadrar(page, orbit, fov, target):
    # dos pasadas: model-viewer interpola el primer jumpCameraToGoal
    for _ in range(2):
        page.evaluate(
            """(a) => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = a.t;
                mv.cameraOrbit = a.o;
                mv.fieldOfView = a.f;
                mv.jumpCameraToGoal();
            }""",
            {"t": target, "o": orbit, "f": fov},
        )
        time.sleep(0.3)


def retratar(page, viewer, nombre, out, salida, vistas=VISTAS, huesos=False, app=True):
    hand = page.evaluate(HAND_TARGET_JS)
    t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
    for vista, (orbit, fov) in vistas.items():
        encuadrar(page, orbit, fov, t)
        salida.setdefault(vista, []).append(
            (nombre, recorte(page, viewer, out / f"{nombre}_{vista}.png", False))
        )
        if huesos:
            salida.setdefault(vista + "_h", []).append(
                (nombre, recorte(page, viewer, out / f"{nombre}_{vista}_h.png", True))
            )
    if app:
        page.evaluate(CAM_PROD_JS)
        time.sleep(0.4)
        salida.setdefault("app", []).append(
            (nombre, recorte(page, viewer, out / f"{nombre}_app.png", False))
        )


def preparar(page):
    page.set_viewport_size({"width": 900, "height": 950})
    time.sleep(0.6)
    free_camera(page)
    return page.query_selector("#viewer")


def publicar(salida, out, cols=4, cell=300):
    out.mkdir(parents=True, exist_ok=True)
    ref = [(n, q) for n, q in REFERENCIAS if q.exists()]
    for vista, imgs in salida.items():
        hoja(ref + imgs, out / f"_{vista}.png", cols=cols, cell=cell)


def anotar(nombre, s):
    print(" ", informe(nombre, s))
