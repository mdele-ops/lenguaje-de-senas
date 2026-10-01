"""Diagnostico de la E del catalogo: como se ve y que tan pareja esta.

Renderiza la pose actual desde la camara de la app y en dos primeros planos, y
imprime las medidas de simetria de `simetria_e`.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from pose_lab_e import free_camera
from search_e10 import CAM_PROD_JS
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, detalle, informe, score_simetria

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "ver_e15"
REF = ROOT / "tools" / "screenshots" / "referencia"

VISTAS = {
    "frente": ("0deg 84deg 0.95m", "22deg"),
    "lado": ("-62deg 84deg 0.95m", "22deg"),
    "abajo": ("0deg 112deg 0.95m", "22deg"),
}


def medir(page, pose):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.45)
    return page.evaluate(SIMETRIA_JS)


def encuadrar(page, orbit, fov, target):
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


def retratos(page, viewer, nombre, salida):
    hand = page.evaluate(HAND_TARGET_JS)
    t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
    for vista, (orbit, fov) in VISTAS.items():
        encuadrar(page, orbit, fov, t)
        for sufijo, overlay in (("", False), ("_h", True)):
            salida.setdefault(vista + sufijo, []).append(
                (
                    nombre,
                    recorte(
                        page, viewer, OUT / f"{nombre}_{vista}{sufijo}.png", overlay
                    ),
                )
            )
    page.evaluate(CAM_PROD_JS)
    time.sleep(0.4)
    salida.setdefault("app", []).append(
        (nombre, recorte(page, viewer, OUT / f"{nombre}_app.png", False))
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    senas = {s["letra"]: s for s in cat["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.6)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        salida = {}
        for letra in ("E", "A", "S"):
            s = medir(page, senas[letra]["pose"])
            print(informe(letra, s), f"score={score_simetria(s):.3f}")
            print(detalle(s))
            if letra == "E":
                retratos(page, viewer, "E_catalogo", salida)
        browser.close()

    ref = [(n, q) for n, q in (
        ("REF foto", REF / "E_usuario2.png"),
        ("REF foto 2", REF / "E_usuario.png"),
    ) if q.exists()]
    for vista, imgs in salida.items():
        hoja(ref + imgs, OUT / f"_{vista}.png", cols=3, cell=320)


if __name__ == "__main__":
    main()
