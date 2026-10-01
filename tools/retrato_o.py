"""Retrata poses de la O y arma las hojas de contactos contra la referencia.

Todas las pruebas de la O miran lo mismo: la camara de la app (que es como la
vera el usuario) y tres primeros planos. Tenerlo en un solo sitio evita que
cada script encuadre distinto y las comparaciones dejen de valer.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from compare_e10 import HAND_TARGET_JS, hoja, recorte
from hoja_e import encuadrar, preparar
from medida_o import MEDIDA_O_JS, detalle, linea, puntuar
from search_e10 import CAM_PROD_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
REF = ROOT / "tools" / "screenshots" / "referencia"

# Orientacion de la mano, la misma idea que en la C: la palma al costado, para
# que el agujero mire a la camara en vez de verse de canto (con la mano de
# frente el area del aro en pantalla cae de 0.21 a 0.02 y la O no se lee).
MUNECA = {"y": 90}
ARM_Z = -18

VISTAS = {
    "frente": ("0deg 84deg 0.85m", "24deg"),
    "lado": ("-55deg 84deg 0.85m", "24deg"),
    "abajo": ("0deg 112deg 0.85m", "24deg"),
}

REFERENCIAS = (("REF foto", REF / "O_usuario.png"), ("REF lamina", REF / "O.png"))


def pose_catalogo(letra="O"):
    cat = json.loads(CATALOGO.read_text("utf-8"))
    return next(s for s in cat["senas"] if s["letra"] == letra)["pose"]


def retratar(casos, out, cols=5, cell=300, vistas=VISTAS, medir=True, huesos=False):
    """casos: lista de (nombre, pose). Devuelve {nombre: medidas}.

    Con `huesos` se anade una hoja con el esqueleto dibujado encima: el
    sombreado de la mano hace muy dificil saber a ojo cual de los bultos es el
    pulgar y donde acaba cada yema.
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    salida, medidas = {}, {}

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        for nombre, pose in casos:
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            page.evaluate(CAM_PROD_JS)
            time.sleep(0.4)
            if medir:
                o = page.evaluate(MEDIDA_O_JS)
                medidas[nombre] = o
                print(linea(nombre, o, puntuar(o)))
                print(detalle(o))
            salida.setdefault("app", []).append(
                (nombre, recorte(page, viewer, out / f"{nombre}_app.png", False))
            )
            hand = page.evaluate(HAND_TARGET_JS)
            t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
            for vista, (orbit, fov) in vistas.items():
                encuadrar(page, orbit, fov, t)
                salida.setdefault(vista, []).append(
                    (nombre, recorte(page, viewer, out / f"{nombre}_{vista}.png", False))
                )
                if huesos:
                    salida.setdefault(vista + "_h", []).append((
                        nombre,
                        recorte(page, viewer, out / f"{nombre}_{vista}_h.png", True),
                    ))
        browser.close()

    ref = [(n, q) for n, q in REFERENCIAS if q.exists()]
    for vista, imgs in salida.items():
        hoja(ref + imgs, out / f"_{vista}.png", cols=cols, cell=cell)
    (out / "_poses.json").write_text(
        json.dumps(dict(casos), ensure_ascii=False, indent=2), "utf-8"
    )
    return medidas
